use super::vector3::Vector3f;
use super::matrix3::Matrix3f;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Matrix4f {
    pub m00: f32, pub m01: f32, pub m02: f32, pub m03: f32,
    pub m10: f32, pub m11: f32, pub m12: f32, pub m13: f32,
    pub m20: f32, pub m21: f32, pub m22: f32, pub m23: f32,
    pub m30: f32, pub m31: f32, pub m32: f32, pub m33: f32,
}

impl Default for Matrix4f {
    fn default() -> Self {
        Self::IDENTITY
    }
}

impl Matrix4f {
    pub const IDENTITY: Self = Self {
        m00: 1.0, m01: 0.0, m02: 0.0, m03: 0.0,
        m10: 0.0, m11: 1.0, m12: 0.0, m13: 0.0,
        m20: 0.0, m21: 0.0, m22: 1.0, m23: 0.0,
        m30: 0.0, m31: 0.0, m32: 0.0, m33: 1.0,
    };

    pub fn from_transform(rot: &Matrix3f, trans: &Vector3f, scale: f32) -> Self {
        Self {
            m00: rot.m00 * scale, m01: rot.m01 * scale, m02: rot.m02 * scale, m03: trans.x,
            m10: rot.m10 * scale, m11: rot.m11 * scale, m12: rot.m12 * scale, m13: trans.y,
            m20: rot.m20 * scale, m21: rot.m21 * scale, m22: rot.m22 * scale, m23: trans.z,
            m30: 0.0, m31: 0.0, m32: 0.0, m33: 1.0,
        }
    }

    pub fn transform_point(&self, p: &Vector3f) -> Vector3f {
        Vector3f {
            x: self.m00 * p.x + self.m01 * p.y + self.m02 * p.z + self.m03,
            y: self.m10 * p.x + self.m11 * p.y + self.m12 * p.z + self.m13,
            z: self.m20 * p.x + self.m21 * p.y + self.m22 * p.z + self.m23,
        }
    }

    pub fn transform_vector(&self, v: &Vector3f) -> Vector3f {
        Vector3f {
            x: self.m00 * v.x + self.m01 * v.y + self.m02 * v.z,
            y: self.m10 * v.x + self.m11 * v.y + self.m12 * v.z,
            z: self.m20 * v.x + self.m21 * v.y + self.m22 * v.z,
        }
    }
}
