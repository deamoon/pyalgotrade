# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import unittest
import datetime
import os

from pyalgotrade.barfeed import ninjatraderfeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.tools import resample
from pyalgotrade import marketsession
from pyalgotrade.utils import dt
from pyalgotrade.dataseries import resampled
from pyalgotrade.dataseries import bards
from pyalgotrade import bar
import common


class ResampleTestCase(unittest.TestCase):
    def testSlotDateTime(self):
        # 1 minute
        self.assertEqual(resampled.get_slot_datetime(datetime.datetime(2011, 1, 1, 1, 1, 1), 60), datetime.datetime(2011, 1, 1, 1, 1))
        self.assertEqual(resampled.get_slot_datetime(datetime.datetime(2011, 1, 1, 1, 1, 1, microsecond=1), 60), datetime.datetime(2011, 1, 1, 1, 1))
        # 5 minute
        self.assertEqual(resampled.get_slot_datetime(datetime.datetime(2011, 1, 1, 1, 0), 60*5), datetime.datetime(2011, 1, 1, 1, 0))
        self.assertEqual(resampled.get_slot_datetime(datetime.datetime(2011, 1, 1, 1, 1), 60*5), datetime.datetime(2011, 1, 1, 1, 0))
        self.assertEqual(resampled.get_slot_datetime(datetime.datetime(2011, 1, 1, 1, 4), 60*5), datetime.datetime(2011, 1, 1, 1, 0))
        self.assertEqual(resampled.get_slot_datetime(datetime.datetime(2011, 1, 1, 1, 5), 60*5), datetime.datetime(2011, 1, 1, 1, 5))
        # 1 hour
        self.assertEqual(resampled.get_slot_datetime(datetime.datetime(2011, 1, 1, 1, 1, 1), 60*60), datetime.datetime(2011, 1, 1, 1))
        self.assertEqual(resampled.get_slot_datetime(datetime.datetime(2011, 1, 1, 1, 1, 1, microsecond=1), 60*60), datetime.datetime(2011, 1, 1, 1))
        # 1 day
        self.assertEqual(resampled.get_slot_datetime(datetime.datetime(2011, 1, 1, 1, 1, 1), 60*60*24), datetime.datetime(2011, 1, 1))
        self.assertEqual(resampled.get_slot_datetime(datetime.datetime(2011, 1, 1, 1, 1, 1, microsecond=1), 60*60*24), datetime.datetime(2011, 1, 1))

    def testResample(self):
        barDs = bards.BarDataSeries()
        resampledBarDS = resampled.ResampledBarDataSeries(barDs, bar.Frequency.MINUTE)

        barDs.append(bar.BasicBar(datetime.datetime(2011, 1, 1, 1, 1, 1), 2.1, 3, 1, 2, 10, 1, bar.Frequency.SECOND))
        barDs.append(bar.BasicBar(datetime.datetime(2011, 1, 1, 1, 1, 2), 2, 3, 1, 2.3, 10, 2, bar.Frequency.SECOND))
        barDs.append(bar.BasicBar(datetime.datetime(2011, 1, 1, 1, 2, 1), 2, 3, 1, 2, 10, 2, bar.Frequency.SECOND))

        self.assertEqual(len(resampledBarDS), 1)
        self.assertEqual(resampledBarDS[0].getDateTime(), datetime.datetime(2011, 1, 1, 1, 1))
        self.assertEqual(resampledBarDS[0].getOpen(), 2.1)
        self.assertEqual(resampledBarDS[0].getHigh(), 3)
        self.assertEqual(resampledBarDS[0].getLow(), 1)
        self.assertEqual(resampledBarDS[0].getClose(), 2.3)
        self.assertEqual(resampledBarDS[0].getVolume(), 20)
        self.assertEqual(resampledBarDS[0].getAdjClose(), 2)

        resampledBarDS.pushLast()
        self.assertEqual(len(resampledBarDS), 2)
        self.assertEqual(resampledBarDS[1].getDateTime(), datetime.datetime(2011, 1, 1, 1, 2))
        self.assertEqual(resampledBarDS[1].getOpen(), 2)
        self.assertEqual(resampledBarDS[1].getHigh(), 3)
        self.assertEqual(resampledBarDS[1].getLow(), 1)
        self.assertEqual(resampledBarDS[1].getClose(), 2)
        self.assertEqual(resampledBarDS[1].getVolume(), 10)
        self.assertEqual(resampledBarDS[1].getAdjClose(), 2)

    def testResampleNinjaTraderHour(self):
        common.init_temp_path()

        # Resample.
        feed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
        feed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"))
        resampledBarDS = resampled.ResampledBarDataSeries(feed["spy"], bar.Frequency.HOUR)
        resampledFile = os.path.join(common.get_temp_path(), "hour-nt-spy-minute-2011.csv")
        resample.resample_to_csv(feed, bar.Frequency.HOUR, resampledFile)
        resampledBarDS.pushLast()  # Need to manually push the last stot since time didn't change.

        # Load the resampled file.
        feed = csvfeed.GenericBarFeed(bar.Frequency.HOUR, marketsession.USEquities.getTimezone())
        feed.addBarsFromCSV("spy", resampledFile)
        feed.loadAll()

        self.assertEqual(len(feed["spy"]), 340)
        self.assertEqual(feed["spy"][0].getDateTime(), dt.localize(datetime.datetime(2011, 1, 3, 9), marketsession.USEquities.getTimezone()))
        self.assertEqual(feed["spy"][-1].getDateTime(), dt.localize(datetime.datetime(2011, 2, 1, 1), marketsession.USEquities.getTimezone()))
        self.assertEqual(feed["spy"][0].getOpen(), 126.35)
        self.assertEqual(feed["spy"][0].getHigh(), 126.45)
        self.assertEqual(feed["spy"][0].getLow(), 126.3)
        self.assertEqual(feed["spy"][0].getClose(), 126.4)
        self.assertEqual(feed["spy"][0].getVolume(), 3397.0)
        self.assertEqual(feed["spy"][0].getAdjClose(), None)

        self.assertEqual(len(resampledBarDS), len(feed["spy"]))
        self.assertEqual(resampledBarDS[0].getDateTime(), dt.as_utc(datetime.datetime(2011, 1, 3, 9)))
        self.assertEqual(resampledBarDS[-1].getDateTime(), dt.as_utc(datetime.datetime(2011, 2, 1, 1)))

    def testResampleNinjaTraderDay(self):
        common.init_temp_path()

        # Resample.
        feed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
        feed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"))
        resampledBarDS = resampled.ResampledBarDataSeries(feed["spy"], bar.Frequency.DAY)
        resampledFile = os.path.join(common.get_temp_path(), "day-nt-spy-minute-2011.csv")
        resample.resample_to_csv(feed, bar.Frequency.DAY, resampledFile)
        resampledBarDS.pushLast()  # Need to manually push the last stot since time didn't change.

        # Load the resampled file.
        feed = csvfeed.GenericBarFeed(bar.Frequency.DAY)
        feed.addBarsFromCSV("spy", resampledFile, marketsession.USEquities.getTimezone())
        feed.loadAll()

        self.assertEqual(len(feed["spy"]), 25)
        self.assertEqual(feed["spy"][0].getDateTime(), dt.localize(datetime.datetime(2011, 1, 3), marketsession.USEquities.getTimezone()))
        self.assertEqual(feed["spy"][-1].getDateTime(), dt.localize(datetime.datetime(2011, 2, 1), marketsession.USEquities.getTimezone()))

        self.assertEqual(len(resampledBarDS), len(feed["spy"]))
        self.assertEqual(resampledBarDS[0].getDateTime(), dt.as_utc(datetime.datetime(2011, 1, 3)))
        self.assertEqual(resampledBarDS[-1].getDateTime(), dt.as_utc(datetime.datetime(2011, 2, 1)))
