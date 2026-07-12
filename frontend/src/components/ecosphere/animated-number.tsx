import { useEffect } from "react";
import { animate, motion, useMotionValue, useTransform } from "framer-motion";

interface AnimatedNumberProps {
  value: number;
  duration?: number;
}

export function AnimatedNumber({
  value,
  duration = 0.8,
}: AnimatedNumberProps) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => Math.round(latest));

  useEffect(() => {
    const controls = animate(count, value, {
      duration,
      ease: "easeOut",
    });
    return controls.stop;
  }, [count, value, duration]);

  return <motion.span className="tabular-nums">{rounded}</motion.span>;
}
