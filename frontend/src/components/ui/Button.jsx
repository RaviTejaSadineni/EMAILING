export default function Button({ children, className = '', ...props }) {
  return (
    <button
      className={`rounded-lg bg-gradient-to-r from-electric to-purple px-4 py-2 font-semibold text-white transition hover:scale-105 ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
