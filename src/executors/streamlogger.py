"""\
See `StreamLogger`.
"""
import sys
import logging
import cStringIO
 
 
class StreamLogger(object):
    """
    A helper which intercepts what's written to an output stream
    then sends it, line by line, to a `logging.Logger` instance.

    Usage:

        By overwriting `sys.stdout`:

            sys.stdout = StreamLogger('stdout')
            print 'foo'

        As a context manager:

            with StreamLogger('stdout'):
                print 'foo'
    """
 
    def __init__(self, name, logger=None, unbuffered=False,
                 flush_on_new_line=True):
        """
        ``name``: The stream name to incercept ('stdout' or 'stderr')
        ``logger``: The logger that will receive what's written to the stream.
        ``unbuffered``: If `True`, `.flush()` will be called each time
                        `.write()` is called.
        ``flush_on_new_line``: If `True`, `.flush()` will be called each time
                               `.write()` is called with data containing a
                               new line character.
        """
        self.__name = name
        self.__stream = getattr(sys, name)
        self.__logger = logger or logging.getLogger()
        self.__buffer = cStringIO.StringIO()
        self.__unbuffered = unbuffered
        self.__flush_on_new_line = flush_on_new_line
 
    def write(self, data):
        """Write data to the stream.
        """
        self.__buffer.write(data)
        if self.__unbuffered is True or \
           (self.__flush_on_new_line is True and '\n' in data):
            self.flush()
 
    def flush(self):
        """Flush the stream.
        """
        self.__buffer.seek(0)
        while True:
            line = self.__buffer.readline()
            if line:
                if line[-1] == '\n':
                    line = line[:-1]
                    if line:
                        level, line = self.parse(line)
                        logger = getattr(self.__logger, level)
                        logger(line)
                else:
                    self.__buffer.seek(0)
                    self.__buffer.write(line)
                    self.__buffer.truncate()
                    break
            else:
                self.__buffer.seek(0)
                self.__buffer.truncate()
                break
 
    def parse(self, data):
        """Override me!
        NOTE TO SELF: 
         - Search for +,++,+++ prefix that indicates set -x and log that at DEBUG level instead
        """
        return 'info', data
 
    def isatty(self):
        """I'm not a tty.
        """
        return False
 
    def __enter__(self):
        """Enter the context manager.
        """
        setattr(sys, self.__name, self)
 
    def __exit__(self, exc_type, exc_value, traceback):
        """Leave the context manager.
        """
        setattr(sys, self.__name, self.__stream)
 

def use_logger(name):
    params = {}
    
    # Must use both to actually split the streams
    params['combine_stderr'] = False
    params['pty'] = False

    # Note: We could create a logger for each stream easily, but 
    # 1 - loggers are never garbage collected, so....be careful
    # 2 - there are multiple hosts anyway, why split by stream but
    #     not by host
    # 3 - all package-level run calls use the same name
    # Solution is to use filters or other light mechanism to add
    # more context e.g. {host}, {username}, {port}, {command}, etc
    x = logging.getLogger(name)
    # x.addHandler(logging.FileHandler('logs/docker.txt'))
    out_err = StreamLogger('stdout', logger=x)
    params['stdout'] = out_err
    params['stderr'] = out_err
    return params

def test_with_fabric():
    """Example use of `StreamLogger` to intercept Fabric's output.
    """
    # Setup logger
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    # Intercepts Fabric's output
    from fabric.api import run, env
    env.host_string = sys.argv[1]
    #with StreamLogger('stdout', logger):
    #    run('ls -l')

    run("1>&2 echo testing", combine_stderr=False, pty=False, stderr=StreamLogger('stdout', logger))
 
 
if __name__ == '__main__':
    test_with_fabric()
