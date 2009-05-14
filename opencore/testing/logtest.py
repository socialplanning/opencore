from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
import logging

class LoggingTestCase(FunctionalTestCase, object):
    # Based on LogInterceptor from CMFCore, but a bit easier to use, 
    # and reliably restores the state of the world on teardown.

    # TODO: this should be usable for other tests than Functional ones.

    logged = None
    installed = ()
    level = 0

    def _start_log_capture(self,
                           min_capture_level=logging.INFO,
                           max_capture_level=logging.FATAL,
                           subsystem=''):
        logger = logging.getLogger(subsystem)
        # Need to patch the logger level to force it to handle the
        # messages we want to capture.
        self._old_logger_level, logger.level = logger.level, min_capture_level
        if subsystem in self.installed:
            # we're already handling this logger.
            return
        self.installed += (subsystem,)
        self.min_capture_level = min_capture_level
        self.max_capture_level = max_capture_level
        logger.addFilter(self)

    def filter(self, record):
        # Standard python logging filter API. False = reject this message.
        if self.logged is None:
            self.logged = []
        if record.levelno < self.min_capture_level or \
                record.levelno > self.max_capture_level:
            # pass it along but don't capture it.
            return True
        self.logged.append(record)
        return False  # reject it before any other handlers see it.

    def _stop_log_capture(self, subsystem=''):
        if subsystem not in self.installed:
            return
        logger = logging.getLogger(subsystem)
        logger.removeFilter(self)
        logger.level = self._old_logger_level
        self.installed = tuple([s for s in self.installed if s != subsystem])

    def tearDown(self):
        for subsystem in self.installed:
            self._stop_log_capture(subsystem)
        super(LoggingTestCase, self).tearDown()
