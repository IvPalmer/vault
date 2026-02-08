import MetricasSection from './MetricasSection'
import RecurringSection from './RecurringSection'
import OrcamentoSection from './OrcamentoSection'
import CardsSection from './CardsSection'
import CheckingSection from './CheckingSection'
import ProjectionSection from './ProjectionSection'
import SmartCategorizeBar from './SmartCategorizeBar'
import styles from './MonthlyOverview.module.css'

function MonthlyOverview() {
  return (
    <div className={styles.container}>
      <MetricasSection />
      <SmartCategorizeBar />
      <RecurringSection />
      <OrcamentoSection />
      <CardsSection />
      <CheckingSection />
      <ProjectionSection />
    </div>
  )
}

export default MonthlyOverview
