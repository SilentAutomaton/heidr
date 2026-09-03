# Источники

[HEID//R](../../README.md) · [Документация](README.md) · [English](../en/credits.md)

`HEID//R` целиком стоит на чужой работе, и делать вид, что это не так, было бы
странно. Ниже полный список того, у кого и что взято. Документ каждого модуля
повторяет те строки этих таблиц, которые к нему относятся, чтобы не приходилось
искать здесь.

Различие между двумя первыми разделами существенное. «Перенесённый код» означает,
что исходник действительно попал в этот репозиторий и шапка оригинала осталась в
файле. «Идеи и методы» означает, что не скопировано ни строки: подход был описан
публично, а написан здесь заново.

## Перенесённый код

| Проект | Автор | Лицензия | Что взято |
|---|---|---|---|
| [rtl-entropy](https://github.com/pwarren/rtl-entropy) | Paul Warren | GPL-3.0 | Дебиасинг фон Неймана и отбеливание SHA-512 для сырых радиоотсчётов |
| [drawille](https://github.com/asciimoo/drawille) | asciimoo | GPL-3.0 | Пиксельная отрисовка брайлевскими ячейками |
| [no-more-secrets](https://github.com/bartobri/no-more-secrets) | Brian Barto | GPL-3.0 | Проявление текста после нажатия клавиши |
| [gqrx-ghostbox](https://github.com/DougHaber/gqrx-ghostbox) | Doug Haber | ISC | Режимы развёртки по частотам и задержка на частоте |
| [dreamdir](https://github.com/sobjornstad/dreamdir) | Soren Bjornstad | MIT | Формат журнала: один текстовый файл на запись |
| [asciimatics](https://github.com/peterbrittain/asciimatics) | Peter Brittain | Apache-2.0 | Плазменное поле и вращающаяся шестерня, переписанные под художников |

## Идеи и методы

| Проект | Автор | Лицензия | Что взято |
|---|---|---|---|
| [libraryofbabel.info-algo](https://github.com/librarianofbabel/libraryofbabel.info-algo) | Jonathan Basile | не указана | Обратимая биекция: адрес превращается в текст, текст восстанавливает адрес. Написано заново по опубликованному описанию |
| [ichingshifa](https://github.com/kentang2017/ichingshifa) | kentang2017 | не указана | Подтверждение счёта Да Янь в три перекладывания. Сам метод традиционный и реализован по классическому описанию |
| [randombtc](https://github.com/callebtc/randombtc) | callebtc | не проверена | Брать корень Меркла, а не хэш блока: сложность майнинга загоняет в хэш ведущие нули и вымывает энтропию |
| [drand](https://github.com/drand/drand) | Protocol Labs и другие | Apache-2.0 / MIT | Сцепление каждой записи с предыдущей, чтобы вся история проверялась |
| [retrogram-rtlsdr](https://github.com/r4d10n/retrogram-rtlsdr) | r4d10n | GPL | ASCII-спектр в терминале как регистр экрана прослушивания |
| [astroterm](https://github.com/da-luce/astroterm) | da-luce | MIT | Проекция из прямого восхождения в горизонтальные координаты, звёздная величина в плотность глифа |
| [gum](https://github.com/charmbracelet/gum) и [huh](https://github.com/charmbracelet/huh) | Charm | MIT | Церемониальный словарь: подтвердить, крутить, выбрать, по одному полю на экран |
| [fortune-mod](https://github.com/shlomif/fortune-mod) | Shlomi Fish и другие | ISC | Плоский офлайновый корпус, чтобы прогон не зависел от чужого сайта |
| [Kerykeion](https://github.com/g-battaglia/kerykeion) | Giacomo Battaglia | не проверена | Отдельное форматирование найденного в блок под языковую модель, помимо человекочитаемого вида |
| [Stellium](https://github.com/katelouie/stellium) | katelouie | не проверена | Планетарные часы: семь управителей от восхода до восхода, дневные и ночные считаются отдельно |
| [ddate](https://github.com/bo0ts/ddate) | Druel the Chaotic, Bo Tso | GPL | Перевод в дискордианский календарь |
| [pyradios](https://github.com/andreztz/pyradios) | André P. Santos | MIT | Разрешение хоста Radio Browser через `all.api.radio-browser.info` и обычай называть себя в User-Agent, как просит сама служба |
| [pyradio](https://github.com/coderholic/pyradio) | Ben Dowling | MIT | Просить у каталога станций больше записей, чем нужно, и молча пропускать те, что не отвечают |
| [Pentametron](http://pentametron.com) | Ranjit Bhatnagar | — | Северная звезда: смысл находится в том, что люди сказали случайно, а не порождается |
| [Урок про плазму](http://lodev.org/cgtutor/plasma.html) | Lode Vandevenne | — | Четыре синусоиды, расходящиеся из четырёх точек, — это и есть плазма |
| [cmatrix](https://github.com/abishekvashok/cmatrix) | Abishek V Ashok | GPL-3.0 | Регистр падающих столбцов глифов |
| Игра «Жизнь» Конвея | Джон Конвей, 1970 | общественное достояние | Правила, которые не нам менять |
| [Галерея Joan Stark](https://oldcompcz.github.io/jgs/joan_stark/), [коллекция Christopher Johnson](https://asciiart.website/), [ASCII Art Archive](https://www.asciiart.eu/) | Joan G. Stark и другие | все права защищены | Изучено, но не скопировано: плотность как тон, тень внутри капюшона, лицо из трёх знаков. Их условия требуют сохранять инициалы автора на каждой копии, чего эта лицензия обеспечить не может, поэтому не взято ничего |
| Обфусцированный текст Minecraft | Mojang | — | Регистр мерцающего лозунга: буквы меняются, очертания слов остаются |

## Внешние программы, вызываемые как процессы

Эти программы запускаются как отдельные процессы, а не подключаются к нашему
коду. Поэтому их лицензии на него не распространяются, даже когда речь идёт о
GPL.

| Программа | Лицензия | Кто использует |
|---|---|---|
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | MIT | `stt/whisper_cpp` |
| [vosk-api](https://github.com/alphacep/vosk-api) | Apache-2.0 | `stt/vosk` |
| rtl_sdr, rtl_fm, rtl_power | GPL-2.0 | радиоисточники |
| [rtl_433](https://github.com/merbanan/rtl_433) | GPL-2.0 | `world/ism` |
| [dump1090](https://github.com/antirez/dump1090) | ISC | `world/adsb_local` |
| [noaa-apt](https://github.com/martinber/noaa-apt) | GPL-3.0 | `world/apt` |
| [chafa](https://github.com/hpjansson/chafa) | GPL-3.0 | вывод изображений в терминал |
| [ffmpeg](https://ffmpeg.org/) | LGPL-2.1-or-later либо GPL-2.0-or-later, смотря как собран | `world/net_voice` |

## Зависимости Python

| Пакет | Лицензия |
|---|---|
| [textual](https://github.com/Textualize/textual), rich | MIT |
| [terminaltexteffects](https://github.com/ChrisBuilds/terminaltexteffects) | MIT |
| numpy, requests, tomli-w, sounddevice | BSD или MIT |

## Данные

Публичные сетевые источники источников: лента землетрясений USGS,
blockchain.info, api.adsb.lol, маяк NIST, журналы Certificate Transparency,
libraryofbabel.info, каталог станций
[Radio Browser](https://api.radio-browser.info/). Документ каждого модуля
называет точный адрес и его условия.

Каталог Radio Browser не требует ключа, а собранные им данные — названия, метки,
ссылки на потоки, языки, страны — его сопровождающий передал в общественное
достояние. Сами потоки остаются собственностью тех, кто вещает. Ничего из этого
не сохраняется: звук расшифровывается в памяти и пропадает.

## Имя

Хейд, вёльва из «Прорицания вёльвы». В общественном достоянии примерно тысячу
лет.
