use super::vector3::Vector3f;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Matrix3f {
    pub m00: f32, pub m01: f32, pub m02: f32,
    pub m10: f32, pub m11: f32, pub m12: f32,
    pub m20: f32, pub m21: f32, pub m22: f32,
}

impl Default for Matrix3f {
    fn default() -> Self {
        Self::IDENTITY
    }
}

impl Matrix3f {
    pub const IDENTITY: Self = Self {
        m00: 1.0, m01: 0.0, m02: 0.0,
        m10: 0.0, m11: 1.0, m12: 0.0,
        m20: 0.0, m21: 0.0, m22: 1.0,
    };

    pub const ZERO: Self = Self {
        m00: 0.0, m01: 0.0, m02: 0.0,
        m10: 0.0, m11: 0.0, m12: 0.0,
        m20: 0.0, m21: 0.0, m22: 0.0,
    };

    pub fn from_array(arr: &[f32; 9]) -> Self {
        Self {
            m00: arr[0], m01: arr[1], m02: arr[2],
            m10: arr[3], m11: arr[4], m12: arr[5],
            m20: arr[6], m21: arr[7], m22: arr[8],
        }
    }

    pub fn mult(&self, vec: &Vector3f) -> Vector3f {
        Vector3f {
            x: self.m00 * vec.x + self.m01 * vec.y + self.m02 * vec.z,
            y: self.m10 * vec.x + self.m11 * vec.y + self.m12 * vec.z,
            z: self.m20 * vec.x + self.m21 * vec.y + self.m22 * vec.z,
        }
    }

    pub fn mult_matrix(&self, rhs: &Self) -> Self {
        Self {
            m00: self.m00 * rhs.m00 + self.m01 * rhs.m10 + self.m02 * rhs.m20,
            m01: self.m00 * rhs.m01 + self.m01 * rhs.m11 + self.m02 * rhs.m21,
            m02: self.m00 * rhs.m02 + self.m01 * rhs.m12 + self.m02 * rhs.m22,

            m10: self.m10 * rhs.m00 + self.m11 * rhs.m10 + self.m12 * rhs.m20,
            m11: self.m10 * rhs.m01 + self.m11 * rhs.m11 + self.m12 * rhs.m21,
            m12: self.m10 * rhs.m02 + self.m11 * rhs.m12 + self.m12 * rhs.m22,

            m20: self.m20 * rhs.m00 + self.m21 * rhs.m10 + self.m22 * rhs.m20,
            m21: self.m20 * rhs.m01 + self.m21 * rhs.m11 + self.m22 * rhs.m21,
            m22: self.m20 * rhs.m02 + self.m21 * rhs.m12 + self.m22 * rhs.m22,
        }
    }

    pub fn transpose(&self) -> Self {
        Self {
            m00: self.m00, m01: self.m10, m02: self.m20,
            m10: self.m01, m11: self.m11, m12: self.m21,
            m20: self.m02, m21: self.m12, m22: self.m22,
        }
    }

    pub fn determinant(&self) -> f32 {
        self.m00 * (self.m11 * self.m22 - self.m12 * self.m21)
            - self.m01 * (self.m10 * self.m22 - self.m12 * self.m20)
            + self.m02 * (self.m10 * self.m21 - self.m11 * self.m20)
    }

    pub fn invert(&self) -> Option<Self> {
        let det = self.determinant();
        if det.abs() < 1e-6 {
            return None;
        }
        let inv_det = 1.0 / det;
        Some(Self {
            m00: (self.m11 * self.m22 - self.m12 * self.m21) * inv_det,
            m01: (self.m02 * self.m21 - self.m01 * self.m22) * inv_det,
            m02: (self.m01 * self.m12 - self.m02 * self.m11) * inv_det,

            m10: (self.m12 * self.m20 - self.m10 * self.m22) * inv_det,
            m11: (self.m00 * self.m22 - self.m02 * self.m20) * inv_det,
            m12: (self.m02 * self.m10 - self.m00 * self.m12) * inv_det,

            m20: (self.m10 * self.m21 - self.m11 * self.m20) * inv_det,
            m21: (self.m01 * self.m20 - self.m00 * self.m21) * inv_det,
            m22: (self.m00 * self.m11 - self.m01 * self.m10) * inv_det,
        })
    }
}
