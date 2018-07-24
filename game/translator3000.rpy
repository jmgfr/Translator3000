﻿
init python:

    import json
    from threading import Lock
    from requests import Session
    from shutil import copy as filecopy
    from os import (
        path,
        remove
    )

    class _Translator3000(Session):

        __author__ = u"Vladya"
        __version__ = (1, 3, 0)

        TRANSLATOR_URL = (
            u"https://translate.yandex.net/api/v1.5/tr.json/translate"
        )

        SETTING = path.abspath(
            path.join(
                renpy.config.basedir,
                u"vladya_translator_setting.json"
            )
        )
        DATABASE = path.abspath(
            path.join(
                renpy.config.basedir,
                u"vladya_translator_database.json"
            )
        )

        YANDEX_API_KEY_PLACEHOLDER = (
            u"Write your key here, replacing this text."
        )

        def __init__(self):

            super(self.__class__, self).__init__()

            try:
                self._notags_filter = renpy.translation.notags_filter
            except Exception:
                self._notags_filter = renpy.translation.dialogue.notags_filter

            if not path.isfile(self.SETTING):
                self.__setting = {
                    u"gameLanguage":
                        u"en",
                    u"directionOfTranslation":
                        u"ru",
                    u"yandexTranslatorAPIKey":
                        self.YANDEX_API_KEY_PLACEHOLDER
                }
                self.save_setting()

            if not path.isfile(self.DATABASE):
                self.__database = {}
                self.backup_database()

            with open(self.SETTING, "rb") as _file:
                self.__setting = json.load(_file)

            with open(self.DATABASE, "rb") as _file:
                self.__database = json.load(_file)

            self.__network_lock = Lock()

        def __call__(self, text):

            _start_text = text
            text = self._format_text(text).strip()

            text_translations = self.__database.setdefault(
                self.__setting[u"gameLanguage"],
                {}
            ).setdefault(text, {})

            needLang = self.__setting[u"directionOfTranslation"]
            if needLang in text_translations.iterkeys():
                return text_translations[needLang]

            APIKey = self.__setting.get(u"yandexTranslatorAPIKey", None)
            if (APIKey == self.YANDEX_API_KEY_PLACEHOLDER) or (not APIKey):
                return _start_text

            try:
                with self.__network_lock:
                    req = self.post(
                        self.TRANSLATOR_URL,
                        data={
                            u"key": APIKey,
                            u"text": text,
                            u"lang": self.lang
                        }
                    )
                req.raise_for_status()
                data = req.json().get(u"text", [])
                data = u'\n'.join(data).strip()
                data = self.uni(data)
                if not data:
                    return _start_text

                text_translations[needLang] = data
                self.backup_database()
                return data

            except Exception:
                return _start_text

        @property
        def lang(self):
            return u"{gameLanguage}-{directionOfTranslation}".format(
                **self.__setting
            )

        def save_setting(self):
            self._write_json(json_data=self.__setting, filename=self.SETTING)

        def backup_database(self):
            self._write_json(json_data=self.__database, filename=self.DATABASE)

        @staticmethod
        def _write_json(json_data, filename):

            name, _ = path.splitext(filename)
            backup = u"{0}.backup".format(name)
            with open(backup, "wb") as _file:
                json.dump(json_data, _file, indent=4)
            filecopy(backup, filename)
            remove(backup)

        @staticmethod
        def _substitute(s):
            s = renpy.substitutions.substitute(s)
            if isinstance(s, basestring):
                return s
            return s[0]

        def _format_text(self, s):
            s = self._notags_filter(s)
            s %= renpy.exports.tag_quoting_dict
            s = self._substitute(s)
            return self.uni(s)

        @staticmethod
        def uni(s):
            assert isinstance(s, basestring), u"{0!r} is not a text.".format(s)
            if isinstance(s, str):
                s = s.decode("utf-8", "ignore")
            return s

    config.say_menu_text_filter = _Translator3000()