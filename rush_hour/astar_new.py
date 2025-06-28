def calculate_edge_weight(edge, current_time, vehicle_type):
    # Base weight (distance + historical collision risk)
    base_weight = edge.length * edge.collision_risk
    
    # Rush hour multiplier
    rush_multiplier = get_rush_hour_multiplier(edge, current_time)
    
    # Vehicle-specific adjustments
    vehicle_multiplier = get_vehicle_multiplier(edge, vehicle_type)
    
    # Final weight
    final_weight = base_weight * rush_multiplier * vehicle_multiplier
    
    return final_weight


## will code this myself l8