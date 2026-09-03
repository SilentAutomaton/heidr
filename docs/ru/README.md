# Документация

[HEID//R](../../README.md) · [English](../en/README.md)

У каждого документа есть английский двойник в `docs/en/` под тем же именем.

## Как пользоваться

| Документ | О чём |
|---|---|
| [Установка](install.md) | Linux, macOS, Windows и сборка одним файлом |
| [Клавиши](keys.md) | Вся раскладка, что взято у vim и где они расходятся |
| [Настройки и модули](settings-editor.md) | Два списка внутри программы и команда `:set` |
| [Проверка состояния](checkhealth.md) | Что показывает `:checkhealth` и как это читать |
| [История ввода](history.md) | Прошлые вопросы и команды, которые хранятся порознь |
| [Голосовой ввод](voice-input.md) | Продиктовать вопрос вместо того, чтобы набирать |

## Как устроено

| Документ | О чём |
|---|---|
| [Устройство](architecture.md) | Три слота, контракты, журнал и что бывает, когда модулю нечего ответить |
| [Анимации](animations.md) | Художники, лестница глифов, панель, заголовок окна |
| [Звук](audio.md) | Единственный звуковой путь, выравнивание и владелец громкости |
| [Языковые модели](llm.md) | Поставщики, параметры выборки и то, как просят толкование |
| [Распознавание речи](stt.md) | vosk, whisper.cpp, облачная форма и выбор модели для эфира |
| [Заимствования](credits.md) | Всё взятое у других, с авторами и лицензиями |

## Как дорабатывать

| Документ | О чём |
|---|---|
| [Добавить модуль](module-guide.md) | Один файл, один декоратор, одна функция |
| [Стиль кода](codestyle.md) | Каким коду позволено быть |
| [Тестирование](testing.md) | Что проверяется, что нет и почему |
| [Знак](../brand/README.md) | Цвета, файлы и как пересобрать |

## Модули

Их тридцать два, по документу на каждый, в каталоге [modules/](modules/). Таблицы со
списком и требованиями лежат в [README проекта](../../README.md#modules).

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
[kiwi_voice](modules/kiwi_voice.md)

**Толкования** превращают материал в ответ:
[cutup](modules/cutup.md) ·
[oblique](modules/oblique.md) ·
[iching](modules/iching.md) ·
[tarot](modules/tarot.md) ·
[mute](modules/mute.md) ·
[pythia](modules/pythia.md)
