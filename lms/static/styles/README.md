# CSS Styling for LMS

There are currently four CSS stylesheets generated from CSS and SASS source here:

- `frontend_apps.css`, entry point `frontend_apps.scss`: The CSS to style the (Preact) front-end components. Components have been converted to use Tailwind utility-first styling in most cases.
- `ui-playground.css`, entry point `ui-playground.scss`: Generates styles needed to style the Pattern Library. Currently in flux; mostly converted to Tailwind but with some extra local override classes.
- `lms.css`, entry point `lms.scss`: The styles output from here are used by back-end interfaces (see `lms/templates/base.html.jinja2`). These styles should be reviewed at some point and evaluated for conversion to Tailwind, if feasible.
