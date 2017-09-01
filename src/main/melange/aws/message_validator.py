from base64 import b64decode
from urllib.request import urlopen

import OpenSSL
from OpenSSL.crypto import load_certificate, FILETYPE_PEM, verify

SNS_MESSAGE_TYPE_SUB_NOTIFICATION = "SubscriptionConfirmation"
SNS_MESSAGE_TYPE_NOTIFICATION = "Notification"
SNS_MESSAGE_TYPE_UNSUB_NOTIFICATION = "UnsubscribeConfirmation"


def canonical_message_builder(content, fmt):
    """ Builds the canonical message to be verified.

        Sorts the fields as a requirement from AWS

        Args:
            content (dict): Parsed body of the response
            fmt (list): List of the fields that need to go into the message
        Returns (str):
            canonical message
    """
    m = ""

    for field in sorted(fmt):
        try:
            m += field + "\n" + content[field] + "\n"
        except KeyError:
            # Build with what you have
            pass

    return str(m)


def verify_sns_notification(message):
    """ Takes a notification request from Amazon push service SNS and verifies the origin of the notification.
        This implementation uses OpenSSL Crypto, inspired by the implementation of
        Artur Rodrigues with M2Crypto: http://goo.gl/KAgPPc
        Args:
            message (dictionary):
                The parsed message content
        Returns (bool):
            True if he message passes the verification, False otherwise
    """

    canonical_sub_unsub_format = ["Message", "MessageId", "SubscribeURL", "Timestamp", "Token", "TopicArn", "Type"]
    canonical_notification_format = ["Message", "MessageId", "Subject", "Timestamp", "TopicArn", "Type"]

    content = message
    decoded_signature = b64decode(content["Signature"])

    # Depending on the message type, canonical message format varies: http://goo.gl/oSrJl8
    if message['Type'] == SNS_MESSAGE_TYPE_SUB_NOTIFICATION or message['Type'] == SNS_MESSAGE_TYPE_UNSUB_NOTIFICATION:

        canonical_message = canonical_message_builder(content, canonical_sub_unsub_format)

    elif message['Type'] == SNS_MESSAGE_TYPE_NOTIFICATION:

        canonical_message = canonical_message_builder(content, canonical_notification_format)

    else:
        raise ValueError("Message Type (%s) is not recognized" % message['Type'])

    # Load the certificate and extract the public key
    cert = load_certificate(FILETYPE_PEM, urlopen(content["SigningCertURL"]).read().decode('utf-8'))

    try:
        verify(cert, decoded_signature, str.encode(canonical_message), 'sha1')
    except OpenSSL.crypto.Error as e:
        return False

    return True
