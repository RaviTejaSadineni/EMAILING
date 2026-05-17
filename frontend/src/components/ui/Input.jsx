export default function Input({ className = '', ...props }) {
  return (
    <input
      className={`w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-electric ${className}`}
      {...props}
    />
  )
}
