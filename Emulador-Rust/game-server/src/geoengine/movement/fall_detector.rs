pub struct FallDetector;

impl FallDetector {
    pub const SAFE_FALL_HEIGHT: f32 = 10.0;
    pub const LETHAL_FALL_HEIGHT: f32 = 50.0;

    /// Calculates fall damage based on fallen height and player max HP.
    pub fn calculate_fall_damage(fall_height: f32, max_hp: u32) -> u32 {
        if fall_height <= Self::SAFE_FALL_HEIGHT {
            return 0;
        }

        if fall_height >= Self::LETHAL_FALL_HEIGHT {
            return max_hp; // Lethal splat
        }

        let damage_ratio = (fall_height - Self::SAFE_FALL_HEIGHT) / (Self::LETHAL_FALL_HEIGHT - Self::SAFE_FALL_HEIGHT);
        ((max_hp as f32) * damage_ratio * 0.8) as u32
    }
}
