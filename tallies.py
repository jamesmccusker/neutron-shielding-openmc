def create_tallies(detector_cell):

        tally = openmc.Tally(name="Neutron flux")

        tally.filters = [openmc.CellFilter(detector_cell)]

        tally.scores = ["flux"]

        tallies = openmc.Tallies([tally])

        return tallies
