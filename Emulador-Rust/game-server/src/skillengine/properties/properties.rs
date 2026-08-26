//! Propriedades de Seleção de Alvos de Habilidades (SkillProperties - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;
use crate::entity::Entity;
use crate::skillengine::properties::target_range::TargetRange;
use crate::skillengine::properties::target_relation::TargetRelation;

#[derive(Debug, Clone)]
pub struct SkillProperties {
    pub target_relation: TargetRelation,
    pub target_range: TargetRange,
    pub cast_range: f32,
    pub area_radius: f32,
    pub max_targets: usize,
}

impl Default for SkillProperties {
    fn default() -> Self {
        Self {
            target_relation: TargetRelation::Enemy,
            target_range: TargetRange::OnlyOne,
            cast_range: 25.0,
            area_radius: 0.0,
            max_targets: 1,
        }
    }
}

impl SkillProperties {
    pub fn new(
        target_relation: TargetRelation,
        target_range: TargetRange,
        cast_range: f32,
        area_radius: f32,
        max_targets: usize,
    ) -> Self {
        Self {
            target_relation,
            target_range,
            cast_range,
            area_radius,
            max_targets,
        }
    }

    /// Filtra as entidades candidatas válidas de acordo com alcance, centro e relação
    pub fn select_targets<'a>(
        &self,
        center: &Coord,
        entities: &'a [Entity],
        selected_target_id: u32,
    ) -> Vec<&'a Entity> {
        let mut candidates = Vec::new();

        match self.target_range {
            TargetRange::OnlyOne => {
                if let Some(target) = entities.iter().find(|e| e.id() == selected_target_id && e.is_alive()) {
                    if center.distance(target.location()) <= self.cast_range {
                        candidates.push(target);
                    }
                }
            }
            TargetRange::Area => {
                let radius_sq = self.area_radius * self.area_radius;
                for e in entities.iter().filter(|e| e.is_alive()) {
                    let d = center.distance(e.location());
                    if d * d <= radius_sq {
                        candidates.push(e);
                        if candidates.len() >= self.max_targets {
                            break;
                        }
                    }
                }
            }
            TargetRange::Point | TargetRange::Cone | TargetRange::Line => {
                for e in entities.iter().filter(|e| e.is_alive()) {
                    if center.distance(e.location()) <= self.cast_range {
                        candidates.push(e);
                        if candidates.len() >= self.max_targets {
                            break;
                        }
                    }
                }
            }
        }

        candidates
    }
}
