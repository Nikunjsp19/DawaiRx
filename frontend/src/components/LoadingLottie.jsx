/**
 * Legacy-parity loading animation. Uses same asset as Python: registro.json.
 * Serve asset at public/loading/registro.json (or copy from src/web/static/loading/).
 */
export default function LoadingLottie({ width = 200, height = 250, className = '' }) {
  return (
    <div className={className}>
      <lottie-player
        src="/loading/registro.json"
        background="transparent"
        speed={1}
        style={{ width, height }}
        loop
        autoplay
      />
    </div>
  )
}
