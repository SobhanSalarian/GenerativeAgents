import logo from "../assets/logo/logo-agenteval.png";
import hero from "../assets/banners/hero-micro-macro-evaluation.png";
import macroCoordination from "../assets/banners/macro-coordination-network.png";
import memoryPlanning from "../assets/banners/memory-planning-action-flow.png";
import avatarArtist from "../assets/personas/persona-artist-animator.png";
import avatarLiterature from "../assets/personas/persona-literature-student.png";
import avatarPoet from "../assets/personas/persona-poet.png";
import avatarActor from "../assets/personas/persona-actor-comedian.png";
import avatarMathematician from "../assets/personas/persona-mathematician.png";
import avatarOfficer from "../assets/personas/persona-retired-officer.png";
import avatarChemistryAthlete from "../assets/personas/persona-chemistry-athlete.png";
import avatarTaxLawyer from "../assets/personas/persona-tax-lawyer.png";

export const uiAssets = {
  logo: {
    id: "logo-agenteval",
    src: logo,
    label: "AgentEval logo",
    use: "Navbar, landing page, footer, app identity",
  },
  hero: {
    id: "hero-micro-macro-evaluation",
    src: hero,
    label: "Micro-to-macro human evaluation hero",
    use: "Landing page, study briefing page, dashboard welcome card",
  },
  banners: {
    macroCoordination,
    memoryPlanning,
  },
  personaAvatars: [
    {
      id: "artist-animator",
      name: "Abigail Chen",
      role: "Digital artist and animator",
      src: avatarArtist,
      keywords: ["digital artist", "animator", "interactive art"],
    },
    {
      id: "literature-student",
      name: "Ayesha Khan",
      role: "Literature student",
      src: avatarLiterature,
      keywords: ["literature", "senior thesis", "shakespeare"],
    },
    {
      id: "poet",
      name: "Carlos Gomez",
      role: "Poet and creative writer",
      src: avatarPoet,
      keywords: ["poet", "collection of poetry", "creative writing"],
    },
    {
      id: "actor-comedian",
      name: "Francisco Lopez",
      role: "Actor and comedian",
      src: avatarActor,
      keywords: ["actor", "comedian", "web series", "improvisational comedy"],
    },
    {
      id: "mathematician",
      name: "Giorgio Rossi",
      role: "Mathematician",
      src: avatarMathematician,
      keywords: ["mathematician", "mathematical patterns", "analytical skills"],
    },
    {
      id: "retired-navy-officer",
      name: "Sam Moore",
      role: "Retired navy officer",
      src: avatarOfficer,
      keywords: ["retired navy officer", "military", "local mayor"],
    },
    {
      id: "chemistry-athlete",
      name: "Wolfgang Schulz",
      role: "Chemistry student athlete",
      src: avatarChemistryAthlete,
      keywords: ["chemistry", "student athlete", "competition"],
    },
    {
      id: "tax-lawyer",
      name: "Yuriko Yamamoto",
      role: "Tax lawyer",
      src: avatarTaxLawyer,
      keywords: ["tax lawyer", "tax compliance", "tax laws"],
    },
  ],
};
