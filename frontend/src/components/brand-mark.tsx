import Image from "next/image";
import logo from "@/assets/sealquery-mark.png";
import { cn } from "@/lib/utils";

export function BrandMark({ className }: { className?: string }) {
  return (
    <Image
      src={logo}
      alt=""
      width={36}
      height={36}
      className={cn("size-9 object-contain", className)}
      priority
    />
  );
}
