#! /bin/python2

# (c) 2016 Eric Marriott
# This code uses a slightly modified version of Peter Norvig's lispy.py in conjuction
# with Selenium WebDriver to create a lisp-like interface for Web testing


from __future__ import division

import code
import sys

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

import lispy as lisp


def default_driver():
    driver = webdriver.Chrome('bin/chromedriver')
    driver.implicitly_wait(10)
    driver.set_script_timeout(20)
    return driver


def _is_hashable(x):
    return hasattr(x, "__hash__")


class WebLisp:
    driver_func = None
    driver = None
    driver_started = False
    after_load = {}
    env = lisp.global_env

    def interact(self):
        try:
            code.interact(local=locals())
        except ValueError:
            return None

    def _build_action_chain(self, vars):
        a_c = ActionChains(self.driver)
        for i in vars:
            a_c = i(a_c)
        return a_c

    def get_addtl_funcs(self):
        return {
            'click': lambda x: x.click()
                if self.driver_started
                else None,
            'find-elem': lambda *x: self.driver.find_element(by=x[0], value=x[1])
                if self.driver_started
                else None,
            'find-elems': lambda *x: self.driver.find_elements(by=x[0], value=x[1])
                if self.driver_started
                else None,
            'action-chain': lambda *x: self._build_action_chain(x),
            'action-click': lambda *x: lambda y: y.click(on_element=x[0]
                if len(x) >= 1
                else None),
            'action-click-and-hold': lambda *x: lambda y: y.click_and_hold(on_element=x[0]
                if len(x) >= 1
                else None),
            'action-key-down': lambda x: lambda y: y.key_down(x),
            'action-key-up': lambda x: lambda y: y.key_up(x),
            'action-move-to-elem': lambda x: lambda y: y.move_to_element(x),
            'action-send-keys': lambda *x: lambda y: y.send_keys(x),
            'action-send-keys-to-elem': lambda *x: lambda y: y.send_keys_to_element(x[0], x[1::]),
            'action-move-by-offset': lambda *x: lambda y: y.move_by_offset(x),
            'action-drag-and-drop-by-offset': lambda *x: lambda y: y.drag_and_drop_by_offset(x[0], x[1], x[2]),
            'action-move-to-elem-with-offset': lambda *x: lambda y: y.move_to_element_with_offset(x),
            'action-release': lambda *x: lambda y: y.release(on_element=x[0]
                if len(x) >= 1
                else None),
            'action-context-click': lambda *x: lambda y: y.context_click(on_element=x[0]
                if len(x) >= 1
                else None),
            'action-double-click': lambda *x: lambda y: y.double_click(on_element=x[0]
                if len(x) >= 1
                else None),
            'action-perform': lambda x: x.perform(),
            'select': lambda x: Select(x),
            'select-by-index': lambda *x: x[0].select_by_index(x[1]),
            'select-by-visible-text': lambda *x: x[0].select_by_visible_text(x[1]),
            'select-by-value': lambda *x: x[0].select_by_value(x[1]),
            'str-split': lambda *x: x[0].split() if len(x) == 1 else x[0].split(x[1]),
            'str-join': lambda *x: x[0].join(x[1]),
            'send-keys': lambda *x: x[0].send_keys(x[1]),
            'open': lambda x: self.driver.get(x),
            'bind-attr': lambda *x: self._bind_attr(x[0])
                if len(x) == 1
                else self._bind_attr(x[0], funcname=x[1]),
            '_shell': lambda: self.interact(),
            '|': lambda *x: list(x),
            'dict-build': lambda *x: self._build_dict(x),
            'dict-lookup': lambda *x: x[1][x[0]] \
                if len(x) > 1 and isinstance(x[1], dict) and _is_hashable(x[0])
                else None
        }



    def _build_dict(self, vals):
        d = {}
        for i in vals:
            d[i[0]] = i[1] if len(i) == 2 \
                else None
        return d

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
        self._gen_macros()
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

    def _gen_macros(self):
        lisp._eval(lisp.parse('''(begin

            (define-macro and (lambda args
               (if (null? args) #t
                   (if (= (length args) 1) (car args)
                       `(if ,(car args) (and ,@(cdr args)) #f)))))

            ;; More macros can also go here

        )'''), self.env)

    def _bind_attr(self, name, funcname = None):
        if name in self.env:
            if funcname is None:
                funcname = name
            setattr(self, funcname, self.env[name])
            return True
        else:
            return False


def main():
    x = WebLisp()
    x.repl()


if __name__ == "__main__":
    main()