#! /bin/python2

# (c) 2016 Eric Marriott
# This code uses a slightly modified version of Peter Norvig's lispy.py in conjuction
# with Selenium WebDriver to create a lispy interface for Web testing


from __future__ import unicode_literals, division

import code
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import lispy as lisp


def default_driver():
    driver = webdriver.Chrome('bin/chromedriver')
    driver.implicitly_wait(10)
    driver.set_script_timeout(20)
    return driver


class WebLisp:
    driver_func = None
    driver = None
    driver_started = False
    after_load = {}
    env = lisp.global_env

    def interact(self):
        try:
            code.interact(local=locals())
            return True
        except:
            return False

    def get_addtl_funcs(self):
        return {
            'click': lambda x: x.click() \
                if self.driver_started \
                else None,
            'find-elem': lambda *x: self.driver.find_element(by=x[0], value=x[1]) \
                if self.driver_started \
                else None,
            'find-elems': lambda *x: self.driver.find_elements(by=x[0], value=x[1]) \
                if self.driver_started \
                else None,
            'send-keys': lambda *x: x[0].send_keys(x[1]),
            'open': self.driver.get,
            '_shell': self.interact
        }

    def get_addtl_vars(self):
        return {
            'by-xpath': By.XPATH,
            'by-link-text': By.LINK_TEXT,
            'by-class-name': By.CLASS_NAME,
            'by-css-selector': By.CSS_SELECTOR,
            'by-partial-link-text': By.PARTIAL_LINK_TEXT,
            'by-name': By.NAME,
            'by-tag-name': By.TAG_NAME,
            'arrow-up-key': Keys.ARROW_UP,
            'arrow-down-key': Keys.ARROW_DOWN,
            'arrow-left-key': Keys.ARROW_LEFT,
            'arrow-right-key': Keys.ARROW_RIGHT
        }

    def env_update(self):
        self.env.update(self.get_addtl_vars())
        self.env.update(self.get_addtl_funcs())
        self.env.update(self.after_load)

    def start_driver(self):
        if self.driver_started:
            return False
        else:
            self.driver = self.driver_func()
            self.driver_started = True
            return True

    def stop_driver(self):
        if self.driver_started:
            self.driver.quit()
            self.driver_started = False
            self.driver = None
            return True
        else:
            return False

    def __init__(self, driver_func=default_driver):
        self.driver_func = driver_func
        self.after_load.update({
            'start-driver': lambda: self.start_driver(),
            'stop-driver': lambda: self.stop_driver()
        })
        self.env_update()

    def repl(self, prompt='WebLisp> ', inport=lisp.InPort(sys.stdin), out=sys.stdout):
        "A prompt-read-eval-print loop."
        while True:
            try:
                if prompt:
                    sys.stderr.write(prompt)
                x = lisp.parse(inport)
                if x is lisp.eof_object: return
                val = lisp._eval(x, self.env)
                if val is not None and out:
                    print >> out, lisp.to_string(val)
            except Exception as e:
                print '%s: %s' % (type(e).__name__, e)


def main():
    x = WebLisp()
    x.repl()


if __name__ == "__main__":
    main()
