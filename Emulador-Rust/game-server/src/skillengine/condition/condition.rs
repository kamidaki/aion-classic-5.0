//! Trait Central de Condições de Execução de Skill (Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::skillengine::model::skill_template::SkillTemplate;

pub trait SkillCondition: Send + Sync {
    /// Valida se a condição é satisfeita para conjurar a habilidade
    fn validate(
        &self,
        caster: &Character,
        target: Option<&Entity>,
        template: &SkillTemplate,
    ) -> Result<(), &'static str>;
}
