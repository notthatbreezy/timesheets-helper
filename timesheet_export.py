
from icalendar import Calendar

import pytz

from datetime import date

MONTH_STR = 'may'
MONTH_INT = 05
YEAR = 2016

with open('{}-{}.ics'.format(MONTH_STR, YEAR), 'rb') as cal:
    gcal = Calendar.from_ical(cal.read())

class TimeSheetEntry(object):
    """Represents a timesheet entry
    """

    TZ = 'US/Eastern'

    def __repr__(self):
        if self.project.startswith('Admin'):
            return '< %s (%s hours) >' % (self.project, self.elapsed_time_hours)
        else:
            return '< %s - %s (%s hours) >' % (self.project, self.description, self.elapsed_time_hours)

    def __init__(self, event):
        """Instantiates a timesheet entry object - parses into relevant components

        Arguments:
        - `event`: ical entry
        """
        self.tz = pytz.timezone(self.TZ)
        self.event = event
        self.dt_start = self.get_dt('dtstart')
        self.dt_end = self.get_dt('dtend')

        self.raw_summary = str(event.get('summary'))
        self.project = self.get_project()
        self.description = self.get_description()
        self.elapsed_time_hours = (self.dt_end - self.dt_start).total_seconds()/3600

    def get_dt(self, key):
        """Returns datetime instance for given key on an event"""
        dt = self.event.get(key).dt
        return self.tz.normalize(dt)

    def get_project(self):
        if self.raw_summary.startswith('Admin'):
            return self.raw_summary

        splits = self.raw_summary.split(' -- ')
        if len(splits) == 2:
            return splits[0]
        return self.raw_summary.split(' - ')[0]

    def get_description(self):
        try:
            return self.raw_summary.split(' - ')[1]
        except:
            pass
        try:
            return self.raw_summary.split(' -- ')[1]
        except:
            return self.raw_summary


def calc_summary(day_dict):
    for entry in day_dict['raw']:
        if entry.project in day_dict['summary']:
            day_dict['summary'][entry.project]['hours'] += entry.elapsed_time_hours
            current_description = day_dict['summary'][entry.project]['description']
            day_dict['summary'][entry.project]['description'] = entry.description + ' ' + current_description
        else:
            day_dict['summary'][entry.project] = {'description': entry.description,
                                                  'hours': entry.elapsed_time_hours}



if __name__ == '__main__':
    events = []
    for c in gcal.walk():
        if c.name == 'VEVENT':
            try:
                events.append(TimeSheetEntry(c))
            except:
                pass

    events = [e for e in events if e.dt_start.month == MONTH_INT and e.dt_start.year == YEAR]

    days = {str(d): {'summary': {}, 'raw': []} for d in range(1,32)}
    for e in events:
        day = str(e.dt_start.day)
        days[day]['raw'].append(e)

    for day, attrs in days.items():
        calc_summary(attrs)

    with open('{}-{}.txt'.format(MONTH_STR, YEAR), 'wb') as fh:
        for day in range(1, 31):
            dt = date(YEAR, MONTH_INT, day)
            fh.write('###################################\n')
            fh.write('###################################\n')
            fh.write('Day: %s\n' % dt.strftime("%A - %B %d, %Y"))
            fh.write('--------\n')
            total_hours = 0
            for project, summary in days[str(day)]['summary'].items():
                fh.write('Project: %s\nHours: %s\nDescription: %s\n' % (project, summary['hours'], summary['description']))
                fh.write('--------\n')
                total_hours += summary['hours']

            fh.write('\nTOTAL: %s\n\n' % total_hours)