export default function Card({ children, className = '' }) {
  return <div className={`glass card-3d rounded-xl p-5 ${className}`}>{children}</div>
}
