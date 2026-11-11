import Image from "next/image";
import logo from "@/assets/sealquery-mark.png";
import { cn } from "@/lib/utils";

export function BrandMark({ className }: { className?: string }) {
  return (
    <Image
      src={logo}
      alt=""
      width={56}
      height={40}
      className={cn("h-10 w-14 shrink-0 rounded-xl object-contain", className)}
      priority
    />
  );
}
