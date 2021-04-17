    def identify(self):
        """Get persistent pump properties."""
        # general properties -----------------------------------------------------------
        # firmware
        response = self.write("id")
        if "OK," in response:  # expect OK,<ID> Version <ver>/
            self.version = response.split(",")[1][:-1].strip()
        # pump head
        response = self.write("pi")
        if "OK," in response:
            self.head = response.split(",")[4]
        # max flowrate
        response = self.write("mf")
        if "OK,MF:" in response:  # expect OK,MF:<max_flow>/
            self.max_flowrate = float(response.split(":")[1][:-1])
        # volumetric resolution - used for setting flowrate
        # expect OK,<flow>,<UPL>,<LPL>,<p_units>,0,<R/S>,0/
        response = self.write("cs")
        precision = len(response.split(",")[1].split(".")[1])
        if precision == 2:  # eg. "5.00"
            self.flowrate_factor = -5  # FI takes microliters/min * 10 as ints
        elif precision == 3:  # eg. "5.000"
            self.flowrate_factor = -6  # FI takes microliters/min as ints

        # for pumps that have a pressure sensor ----------------------------------------
        # pressure units
        response = self.write("pu")
        if "OK," in response:  # expect "OK,<p_units>/"
            self.pressure_units = response.split(",")[1][:-1]
        # max pressure
        response = self.write("mp")
        if "OK,MP:" in response:  # expect "OK,MP:<max_pressure>/"
            self.max_pressure = float(response.split(":")[1][:-1])
