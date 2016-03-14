#!/usr/bin/env python3

import logging
import logging.handlers
import configparser
import multiprocessing
import sys


from mymongolib import utils
from mymongolib import mysql
from mymongolib.mongodb import MyMongoDB
from importlib import util

config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger('mymongo')
logger.setLevel(logging.getLevelName(config['log']['console_level']))
logformatter = logging.Formatter('%(asctime)s;%(levelname)s;%(message)s')
fh = logging.handlers.TimedRotatingFileHandler('logs/mymongo.log', 'midnight', 1, backupCount=10)
fh.setLevel(logging.getLevelName(config['log']['file_level']))
fh.setFormatter(logformatter)
ch = logging.StreamHandler()
ch.setLevel(logging.getLevelName(config['log']['console_level']))
ch.setFormatter(logformatter)
logger.addHandler(fh)
logger.addHandler(ch)

if __name__ == '__main__':
    logger.info('Start mymongo')
    parser = utils.cmd_parser()
    args = parser.parse_args()
    mongo = MyMongoDB(config['mongodb'])
    if args.mysqldump_data:
        try:
            utils.run_mysqldump(dump_type='data', conf=config['mysql'], mongodb=mongo)
            logger.info('Data dump procedure ended')
            sys.exit(0)
        except Exception as e:
            logger.error('Data dump procedure ended with errors: ' + str(e))
            sys.exit(1)

    if args.daemon:
        try:
            util.find_spec('setproctitle')
            import setproctitle
            setproctitle.setproctitle('mymongo_daemon')
        except ImportError:
            logger.info('Cannot set process name')

        mongo = MyMongoDB(config['mongodb'])
        processes = list()
        processes.append(multiprocessing.Process(target=mysql.mysql_stream, args=(config['mysql'], mongo)))
        for process in processes:
            process.start()
            process.join()
        # mysql.mysql_stream(config['mysql'], mongo)