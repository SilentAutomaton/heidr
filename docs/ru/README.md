# Документация

[HEID//R](../../README.md) · [English](../en/README.md)

У каждого документа здесь есть английский двойник в `docs/en/` с тем же именем
файла.

## Как этим пользоваться

| Документ | Что внутри |
|---|---|
| [Установка](install.md) | Linux, macOS, Windows и сборка одним файлом |
| [Клавиши](keys.md) | Вся раскладка, что взято у вима и где с ним разошлись |
| [Настройки и модули](settings-editor.md) | Два списка внутри программы и команда `:set` |
| [Проверка](checkhealth.md) | Что показывает `:checkhealth` и как это читать |
| [История ввода](history.md) | Прошлые вопросы и команды, хранятся порознь |
| [Голосовой ввод](voice-input.md) | Как продиктовать вопрос вместо того, чтобы набирать |

## Как оно устроено

| Документ | Что внутри |
|---|---|
| [Устройство](architecture.md) | Три слота, договоры между ними, журнал и что бывает, когда модулю нечего ответить |
| [Анимации](animations.md) | Отрисовщики, лестница глифов, панель, заголовок окна |
| [Звук](audio.md) | Одна дорога наружу, выравнивание и кому принадлежит громкость |
| [Языковые модели](llm.md) | Поставщики, параметры выборки и как просят толкование |
| [Распознавание речи](stt.md) | vosk, whisper.cpp, облачная форма и какая модель нужна для эфира |
| [Источники](credits.md) | Все заимствования, с авторами и лицензиями |

## Если вы это дорабатываете

| Документ | Что внутри |
|---|---|
| [Как добавить модуль](module-guide.md) | Один файл, один декоратор, одна функция |
| [Стиль кода](codestyle.md) | Каким коду разрешено быть |
| [Тесты](testing.md) | Что проверяется, что нет и почему |
| [Логотип](../brand/README.md) | Цвета, файлы и как всё это пересобрать |

## Модули

Их тридцать три, по документу на каждый, в каталоге [modules/](modules/).
Таблицы со всем, что каждому из них нужно, лежат в
[README проекта](../../README.md#modules).

**Модули вопроса** превращают вопрос в ключ:
[gematria](modules/gematria.md) ·
[skeleton](modules/skeleton.md) ·
[acrostic](modules/acrostic.md) ·
[rarest](modules/rarest.md) ·
[blind](modules/blind.md) ·
[moment](modules/moment.md) ·
[calendar](modules/calendar.md) ·
[planetary](modules/planetary.md) ·
[reversal](modules/reversal.md) ·
[embed](modules/embed.md)

**Источники** добывают материал:
[mojibake](modules/mojibake.md) ·
[babel](modules/babel.md) ·
[quake](modules/quake.md) ·
[chain](modules/chain.md) ·
[sky](modules/sky.md) ·
[sdr_noise](modules/sdr_noise.md) ·
[rtl_peak](modules/rtl_peak.md) ·
[ism](modules/ism.md) ·
[adsb_local](modules/adsb_local.md) ·
[hline](modules/hline.md) ·
[apt](modules/apt.md) ·
[fm_voice](modules/fm_voice.md) ·
[sw_voice](modules/sw_voice.md) ·
[mw_voice](modules/mw_voice.md) ·
[net_voice](modules/net_voice.md) ·
[kiwi_voice](modules/kiwi_voice.md) ·
[twitch_voice](modules/twitch_voice.md)

**Толкования** превращают материал в ответ:
[cutup](modules/cutup.md) ·
[oblique](modules/oblique.md) ·
[iching](modules/iching.md) ·
[tarot](modules/tarot.md) ·
[mute](modules/mute.md) ·
[pythia](modules/pythia.md)
