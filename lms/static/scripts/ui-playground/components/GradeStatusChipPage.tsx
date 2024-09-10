import { DataTable } from '@hypothesis/frontend-shared';
import Library from '@hypothesis/frontend-shared/lib/pattern-library/components/Library';

import GradeStatusChip from '../../frontend_apps/components/dashboard/GradeStatusChip';

export default function GradeStatusChipPage() {
  return (
    <Library.Page title="Grade status chip">
      <Library.Section title="GradeStatusChip">
        <p>
          It renders a badge with an automatically calculating color
          combination, based on a grade from 0 to 100.
        </p>
        <Library.Demo withSource>
          <GradeStatusChip grade={100} />
          <GradeStatusChip grade={80} />
          <GradeStatusChip grade={68} />
          <GradeStatusChip grade={38} />
          <GradeStatusChip grade={0} />
          <GradeStatusChip grade={120} />
          <GradeStatusChip grade={-25} />
        </Library.Demo>
      </Library.Section>

      <Library.Section title="GradeStatusChip in DataTable">
        <p>
          We plan to use the <code>GradeStatusChip</code> inside the dashboard
          metrics tables. This is how it will look like.
        </p>
        <Library.Demo withSource>
          <DataTable
            grid
            striped={false}
            rows={[
              {
                name: 'Bethany VonRueden',
                grade: 100,
                annotations: 4,
                replies: 1,
              },
              {
                name: 'Grace Feet',
                grade: 92,
                annotations: 2,
                replies: 1,
              },
              {
                name: 'Hannah Rohan',
                grade: 0,
                annotations: 0,
                replies: 0,
              },
              {
                name: 'Jeremiah Kassuke',
                grade: 68,
                annotations: 1,
                replies: 2,
              },
              {
                name: 'Julio Mertz',
                grade: 75,
                annotations: 2,
                replies: 1,
              },
              {
                name: 'Martha Russel',
                grade: 48,
                annotations: 1,
                replies: 0,
              },
            ]}
            columns={[
              {
                field: 'name',
                label: 'Student',
              },
              {
                field: 'grade',
                label: 'Grade',
              },
              {
                field: 'annotations',
                label: 'Annotations',
              },
              {
                field: 'replies',
                label: 'Replies',
              },
            ]}
            title="Students"
            renderItem={(row, field) => {
              if (field === 'grade') {
                return <GradeStatusChip grade={row.grade} />;
              }

              return row[field];
            }}
          />
        </Library.Demo>
      </Library.Section>
    </Library.Page>
  );
}
