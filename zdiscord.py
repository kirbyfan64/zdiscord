# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from logbook import RotatingFileHandler, StreamHandler, Logger
from discord.ext import commands

import functools, inspect, os, sys, traceback, yaml
from pathlib import Path


__all__ = ['loadfile', 'Config', 'safe_command', 'Bot', 'main']


def loadfile(path):
    with Path(path).open() as f:
        return yaml.load(f)


class Config:
    EXPANDS = []

    def __init__(self, path=None):
        if path is None:
            path = self.DEFAULT_PATH

        self.path = os.path.expanduser(path)
        self.data = loadfile(self.path)

    def __getattr__(self, name):
        if name not in self.data:
            raise AttributeError(name)
        value = self.data[name]
        if name in self.EXPANDS:
            return os.path.expandvars(value)
        else:
            return value


def safe_command(func):
    @functools.wraps(func)
    async def wrapper(self, *args):
        try:
            return await func(self, *args)
        except Exception as ex:
            self.logger.error(f'Fatal error inside {func.__name__}!!!!')
            self.logger.error(traceback.format_exc())
            self.logger.error(str(ex))

            await self.bot.say(f'''
*BOOOOOOOM*

Unfortunately, this bot crashed while running your command. After the
flames and screaming, this info was left behind:

Function where the error occurred: `{func.__name__}`

```
{traceback.format_exc()}
```

Sorry! :(
'''.strip())

    pass_context = 'ctx' in inspect.getfullargspec(func).args
    return commands.command(name=func.__name__, pass_context=pass_context)(wrapper)


class Bot(commands.Bot):
    def __init__(self, config):
        super(Bot, self).__init__(command_prefix=self.COMMAND_PREFIX)
        self.config = config
        self.logger = Logger(self.__class__.__name__.lower())
        self.event(self.on_ready)
        self.add_cog(self.COMMANDS(self))

    def run(self):
        super(Bot, self).run(self.config.token)

    async def on_ready(self):
        self.logger.info(f'Logged in: {self.user.name} {self.user.id}')


def main(botcls, config):
    if 'logfile' in config.data:
        handler = RotatingFileHandler(os.path.expanduser(config.logfile))
    else:
        handler = StreamHandler(sys.stdout)

    handler.push_application()

    bot = botcls(config)
    bot.run()
