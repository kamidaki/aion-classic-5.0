use crate::geoengine::math::Vector3f;
use crate::geoengine::models::GeoMap;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct MovementValidationResult {
    pub is_valid: bool,
    pub adjusted_pos: Vector3f,
    pub reason: Option<&'static str>,
}

pub struct MovementValidator;

impl MovementValidator {
    pub const MAX_RUN_SPEED: f32 = 12.0; // m/s with speed buffs/scrolls
    pub const MAX_FLY_SPEED: f32 = 18.0; // m/s
    pub const MAX_STEP_HEIGHT: f32 = 2.5; // max vertical step up in 1 tick

    pub fn validate_step(
        geo_map: &GeoMap,
        current_pos: &Vector3f,
        target_pos: &Vector3f,
        elapsed_sec: f32,
        is_flying: bool,
        is_gliding: bool,
    ) -> MovementValidationResult {
        let max_speed = if is_flying || is_gliding {
            Self::MAX_FLY_SPEED
        } else {
            Self::MAX_RUN_SPEED
        };

        let distance_3d = current_pos.distance(target_pos);
        let max_allowed_dist = (max_speed * elapsed_sec) + 1.0; // 1.0m tolerance for network jitter

        if distance_3d > max_allowed_dist && elapsed_sec > 0.05 {
            return MovementValidationResult {
                is_valid: false,
                adjusted_pos: *current_pos,
                reason: Some("SpeedLimitExceeded"),
            };
        }

        // Check if movement path is blocked by solid geometry
        if !geo_map.can_see(current_pos, target_pos) {
            return MovementValidationResult {
                is_valid: false,
                adjusted_pos: *current_pos,
                reason: Some("CollisionBlocked"),
            };
        }

        // On ground, validate ground height
        if !is_flying && !is_gliding {
            let ground_z = geo_map.get_z(target_pos.x, target_pos.y, Some(target_pos.z));
            let vertical_delta = target_pos.z - current_pos.z;

            if vertical_delta > Self::MAX_STEP_HEIGHT && (target_pos.z - ground_z) > 1.0 {
                return MovementValidationResult {
                    is_valid: false,
                    adjusted_pos: Vector3f::new(target_pos.x, target_pos.y, ground_z),
                    reason: Some("StepHeightExceeded"),
                };
            }

            return MovementValidationResult {
                is_valid: true,
                adjusted_pos: Vector3f::new(target_pos.x, target_pos.y, ground_z),
                reason: None,
            };
        }

        MovementValidationResult {
            is_valid: true,
            adjusted_pos: *target_pos,
            reason: None,
        }
    }
}
