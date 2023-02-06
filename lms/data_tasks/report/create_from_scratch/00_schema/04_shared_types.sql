DROP TYPE IF EXISTS report.tree_relation;

CREATE TYPE report.tree_relation AS ENUM ('self', 'parent', 'ancestor');