![melange logo](img/melange_logo.png)

<p align="center">
    <em>The spice must flow</em>
</p>

---

**Melange** is a python library/framework that abstracts a lot of the boilerplate that is usually 
required to implement a messaging infrastructure (commonly used to create distributed architectures 
and interact with microservices architectures).

Out of the box Melange supports Amazon SQS + SNS, though the library is designed to be extensible, so that you
can use it with your own messaging infrastructure, should you choose so.

The interface this library offers is very clean and tries to tightly follow the best practices from Vaughn Vernon's book
[Implementing Domain-Driven Design](https://www.amazon.es/Implementing-Domain-Driven-Design-Vaughn-Vernon/dp/0321834577)
as well as the recommended design patterns when dealing with messaging on distributed architectures.

## Installing ##

```
pip install melange
```

## Documentation

Full documentation is available at [https://rydra.github.io/melange/](https://rydra.github.io/melange/)

## Why the name 'Melange'

The name "Melange" is a reference to the drug-spice from the sci-fi book saga "Dune", a spice which is only 
generated in a single planet in the universe (planet Dune) and every human depends on it.

>If the spice flows, then the spice can be controlled.  
He who controls the spice, controls the universe.  
The spice must flow.

The analogy can be very well made on Events in a distributed architecture :)

## Project Links

* Docs: [https://rydra.github.io/melange](https://rydra.github.io/melange)

## License

MIT licensed. See the bundled [LICENSE](https://github.com/Rydra/melange/blob/master/LICENSE) file for more details.


_Logo <a href="https://www.vecteezy.com/free-vector/nature">Nature Vectors by Vecteezy</a>_
