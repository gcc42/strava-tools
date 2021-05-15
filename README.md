strava-tools
============

Library for web-scraping Strava data.

> This library became as a fork from [loisaidasam/stravalib-scraper](https://github.com/loisaidasam/stravalib-scraper) with some extentions
> - a shell
> - load following activity feed
> - **send batch kudos**
> - display / filter activities

Note: Strava does have a [developer portal](https://developers.strava.com/) complete with a proper API and examples. This web-scraping based library is written to complete the lack of feature of the standard API. Accessing Friends' acitivities and interations with them like kudoing.


Installation via PyPi:
-------------

```
$ pip install strava-tools
```

Command line:
-----------------------

To simply start the strava shell:

```
$ strava-shell
strava >>
```
Here is basic example on how to display, load and send kudos to people as batch

```
strava >> login
Username:
Password:
Remember session ? [Y/n]:
strava >> load --all
Loaded 149 activities
strava >> activities
Activities 171/171
Kudo Time                 Athlete               Sport Duration Distance Elevation Velocity Title
----+--------------------+---------------------+-----+--------+--------+---------+--------+--------------------------------
     2019-03-27 08:42:06  J************         Sport 11h 26m  2.54 km                     Marche matinale
✓    2019-03-27 09:14:07  N************         Bike  26m 47s  12.00 km           26.9 kmh Vélo au fit
✓    2019-03-27 10:49:02  L****** P*****        Ski   4h 45m   57.38 km                    Skiing in Norefjell with friends
✓    2019-03-27 11:48:03  M****** M*****        Run   1h 41m   19.00 km           5'18     Lunch Run
     2019-03-27 16:29:06  J***** B******        Bike  49m 51s  16.98 km           20.4 kmh Sortie à vélo dans l'après-midi
✓    2019-03-27 16:55:05  L*** A*****           Bike  58m 03s  33.29 km           34.4 kmh Mistral gagnant
✓    2019-03-27 17:16:00  R***** D****          Run   41m 07s  7.83 km            5'15     Evening Run
✓    2019-03-27 17:22:55  A******** N******     Run   57m 23s  8.60 km            6'40     Evening Run
     2019-03-27 17:30:12  J***** M*****         Sport 1h 00m                               Bodybalance
✓    2019-03-27 21:23:21  C**** P****           Sport 29m 00s                              Night Activity
strava >> kudo
Kudoing J******** for Marche matinale .. Ok
Kudoing J***** B****** for Sortie à vélo dans l'après-midi .. Ok
Kudoing J***** M***** for Night Activity .. Ok
```
