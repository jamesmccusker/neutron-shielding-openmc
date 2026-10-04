
def create_settings(source_distance,shield_height,source_energy,particles,batches):

        settings = openmc.Settings()

        settings.run_mode = "fixed source"

        settings.batches = batches

        settings.particles = particles

        source = openmc.IndependentSource()

        source.space = openmc.stats.Point((-source_distance, shield_height/2, shield_height/2))

        #Neutron energy

        source.energy = openmc.stats.Discrete([source_energy * 1e6], [1.0])

        #Neutrons emitted in all directions
        source.angle = openmc.stats.Monodirectional((1,0,0))

        settings.source = source

        return settings
