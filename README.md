# bitstream-tools
Tools for manuipulating and analysing digital data from test equipment

The first (rough) draft was built to handle  output packets captured with [Universal Radio hacker](https://github.com/jopohl/urh)
It is optimised entrely for Pulse Interval Encoding. (See the notes in the samples readme for details and references)

There's probably a way to do this inside the application itself, but I haven't figured that out yet.

At present it only handles unsigned 16 bit data files.

### Analysing data files

You use it by running:
```python signal_demod.py```

### analysing a screen capture

An extra utility uses the same underlying algorithm to read the values from a screen capture.
This is somehwat clunkily based on thed default colours and could use some tweaking, but gives 
identical results to analysing the data files for the same three data sets.

Sample images provided.

You can use it by running:
```python image_scanner.py```
