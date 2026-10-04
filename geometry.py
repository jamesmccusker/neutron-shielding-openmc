def geometry(
    air,
    materials,
    thicknesses,
    shield_height,
    source_distance,
    detector_gap,
    detector_thickness,
    air_before,
    air_after
):
    # Create shielding material cells

    material_regions = []
    material_cells = []

    x_position = 0

    y1 = openmc.YPlane(y0=0)
    y2 = openmc.YPlane(y0=shield_height)

    z1 = openmc.ZPlane(z0=0)
    z2 = openmc.ZPlane(z0=shield_height)

    for i, (material, thickness) in enumerate(zip(materials, thicknesses)):

        if thickness <= 0:
            continue

        x_start = x_position
        x_end = x_position + thickness

        x1 = openmc.XPlane(x0=x_start)
        x2 = openmc.XPlane(x0=x_end)

        material_region = (+x1 & -x2 & +y1 & -y2 & +z1 & -z2)

        material_cell = openmc.Cell(name=f"Material {i + 1}", region=material_region, fill=material)

        material_regions.append(material_region)
        material_cells.append(material_cell)

        x_position = x_end

    # Detector

    detector_x1 = openmc.XPlane(x0=x_position + detector_gap)

    detector_x2 = openmc.XPlane(x0=x_position + detector_gap + detector_thickness)

    detector_region = (+detector_x1 & -detector_x2 & +y1 & -y2 & +z1 & -z2)

    detector_cell = openmc.Cell(name="Detector", region=detector_region, fill=air)

    # Outer boundaries

    left_boundary = openmc.XPlane(x0=-source_distance - air_before, boundary_type="vacuum")

    right_boundary = openmc.XPlane(x0=x_position + detector_gap + detector_thickness + air_after, boundary_type="vacuum")

    front_boundary = openmc.YPlane(y0=-10, boundary_type="vacuum")

    back_boundary = openmc.YPlane(y0=shield_height + 10, boundary_type="vacuum")

    lower_boundary = openmc.ZPlane(z0=-10, boundary_type="vacuum")

    upper_boundary = openmc.ZPlane(z0=shield_height + 10, boundary_type="vacuum")

    # Outer air region

    outer_region = (+left_boundary & -right_boundary & +front_boundary & -back_boundary & +lower_boundary & -upper_boundary)

    air_region = outer_region & ~detector_region

    for material_region in material_regions:
        air_region = air_region & ~material_region

    air_cell = openmc.Cell(name="Air", region=air_region, fill=air)

    # Universe

    universe = openmc.Universe(cells=[air_cell, *material_cells, detector_cell])

    return universe, detector_cell
