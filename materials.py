import openmc


def create_materials():

    air = openmc.Material(name="Air")
    air.set_density("g/cm3", 0.001225)

    air.add_element("N", 0.755, "wo")
    air.add_element("O", 0.232, "wo")
    air.add_element("Ar", 0.013, "wo")

    concrete = openmc.Material(name="Concrete")
    concrete.set_density("g/cm3", 2.3)

    concrete.add_element("H", 0.01, "wo")
    concrete.add_element("O", 0.52, "wo")
    concrete.add_element("Si", 0.34, "wo")
    concrete.add_element("Ca", 0.08, "wo")
    concrete.add_element("Al", 0.03, "wo")
    concrete.add_element("Fe", 0.02, "wo")

    water = openmc.Material(name="Water")
    water.set_density("g/cm3", 1.0)
    water.add_element("H", 0.1119, "wo")
    water.add_element("O", 0.8881, "wo")

    steel = openmc.Material(name="Steel")
    steel.set_density("g/cm3", 7.8)
    steel.add_element("Fe", 0.98, "wo")
    steel.add_element("C", 0.02, "wo")

    materials = {
        "air":air,
        "concrete": concrete,
        "water": water,
        "steel": steel,
    }

    return materials
