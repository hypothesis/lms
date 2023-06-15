DROP SCHEMA IF EXISTS h CASCADE;
-- Keep foreign tables on its own schema
CREATE SCHEMA h;

-- These types are required to successfully import the group table
DROP TYPE IF EXISTS public.group_joinable_by;
CREATE TYPE public.group_joinable_by AS ENUM (
    'authority'
);

DROP TYPE IF EXISTS public.group_readable_by;
CREATE TYPE public.group_readable_by AS ENUM (
    'authority', 'members', 'world'
);

DROP TYPE IF EXISTS public.group_writeable_by;
CREATE TYPE public.group_writeable_by AS ENUM (
    'authority', 'members'
);

DROP TYPE IF EXISTS public.annotation_sub_type;
CREATE TYPE report.annotation_sub_type AS ENUM (
    'annotation', 'reply', 'highlight', 'page_note'
);

IMPORT FOREIGN SCHEMA "public" LIMIT TO (
    user_group,
    "user",
    "group"
) FROM SERVER "h_server" INTO h;

IMPORT FOREIGN SCHEMA "report" LIMIT TO (
    authorities,
    annotation_group_counts,
    annotation_type_group_counts,
    annotation_user_counts
) FROM SERVER "h_server" INTO h;
