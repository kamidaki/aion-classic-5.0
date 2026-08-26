//! Lista de Criaturas Visíveis no Campo de Visão (SeenCreatureList - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashSet;

#[derive(Debug, Clone, Default)]
pub struct SeenCreatureList {
    pub seen_objects: HashSet<u32>,
}

impl SeenCreatureList {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add(&mut self, obj_id: u32) -> bool {
        self.seen_objects.insert(obj_id)
    }

    pub fn remove(&mut self, obj_id: u32) -> bool {
        self.seen_objects.remove(&obj_id)
    }

    pub fn contains(&self, obj_id: u32) -> bool {
        self.seen_objects.contains(&obj_id)
    }

    pub fn clear(&mut self) {
        self.seen_objects.clear();
    }
}
