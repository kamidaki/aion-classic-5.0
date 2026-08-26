pub const PI: f32 = std::f32::consts::PI;
pub const TWO_PI: f32 = std::f32::consts::PI * 2.0;
pub const HALF_PI: f32 = std::f32::consts::FRAC_PI_2;
pub const DEG_TO_RAD: f32 = PI / 180.0;
pub const RAD_TO_DEG: f32 = 180.0 / PI;

#[inline]
pub fn clamp(val: f32, min: f32, max: f32) -> f32 {
    if val < min {
        min
    } else if val > max {
        max
    } else {
        val
    }
}

#[inline]
pub fn lerp(a: f32, b: f32, t: f32) -> f32 {
    a + (b - a) * t
}

#[inline]
pub fn heading_to_angle(heading: u8) -> f32 {
    (heading as f32) * (360.0 / 120.0) * DEG_TO_RAD
}

#[inline]
pub fn angle_to_heading(angle_rad: f32) -> u8 {
    let mut deg = angle_rad * RAD_TO_DEG;
    while deg < 0.0 {
        deg += 360.0;
    }
    while deg >= 360.0 {
        deg -= 360.0;
    }
    (deg / 3.0).round() as u8
}
