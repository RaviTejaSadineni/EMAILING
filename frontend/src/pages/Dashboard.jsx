import Card from '../components/ui/Card'

const kpis = [
  { title: 'Contracts in Flight', value: '128' },
  { title: 'Avg Cycle Time', value: '19.4 days' },
  { title: 'SLA Breach Rate', value: '20.5%' },
  { title: 'Negotiation Loop', value: '7.3 days' },
]

export default function Dashboard() {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Analytics Dashboard</h2>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi) => (
          <Card key={kpi.title}>
            <p className="text-sm text-white/70">{kpi.title}</p>
            <p className="mt-2 text-2xl font-bold text-electric">{kpi.value}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}
