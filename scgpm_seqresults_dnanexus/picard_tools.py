
class CollectAlignmentSummaryMetrics:
    def __init__(self, fh):
        """
        Parses the metrics output by Picard CollectAlignmentSummaryMetrics into a dict that is stored
        in self.metrics. 

        Args:
            fh: A file handle for reading. 
        """
        self.fh = fh
        #: Sets self.metrics, and also sets self.header.
        self._parse()

    def _parse(self):
        # Read past the comment lines
        while True:
            line = self.fh.readline().rstrip("\n")
            if not line:
                continue
            if line.startswith("#"):
                 continue
            break
        # Now we're on the header line
        header = line.rstrip("\n").split("\t")
        self.header = header[1:] #leave off CATEGORY field
        #The next 3 lines are FIRST_OF_PAIR stats, SECOND_OF_PAIR stats, and PAIR stats.
        self.metrics = {}
        for i in range(3):
            self._parseMetricsLine(self.fh.readline())

    def _parseMetricsLine(self,line):
        line = line.rstrip("\n").split("\t")
        category = line[0]
        attrs = line[1:]
        self.metrics[category] = {}
        for fieldNum in range(len(self.header)):
            fieldName = self.header[fieldNum]
            attrVal = attrs[fieldNum]
            self.metrics[category][fieldName] = attrVal
