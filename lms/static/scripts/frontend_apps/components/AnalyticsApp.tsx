import { useParams } from 'wouter-preact';

export default function AnalyticsApp() {
  const params = useParams();
  return <div>Analytics miniapp for {params.instanceId}</div>;
}
