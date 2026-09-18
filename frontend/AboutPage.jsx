import React, { useEffect, useRef } from 'react';
import { ArrowRight } from 'lucide-react';
import portrait from './assets/christoph-scharnagl.png';
import './about-landing.css';
import './action-motion.css';
import './privacy.css';

// Research/bio: supplied presentation, slides 1, 11, 12.
// Contact: https://www.th-nuernberg.de/person/scharnagl-christoph/
// Institute/address: official IFAI team and contact page (see README).
export default function AboutPage() {
  const heading = useRef(null);
  useEffect(() => { heading.current?.focus({ preventScroll: true }); }, []);
  return <main className="about-page about-landing">
    <div className="about-content">
      <div className="about-landing-intro">
      <section className="about-project" aria-labelledby="about-title">
        <span className="eyebrow">DAS FORSCHUNGSPROJEKT</span>
        <h1 id="about-title" ref={heading} tabIndex={-1}>Das Forschungsprojekt DIANA</h1>
        <div className="about-project-body">
          <div className="about-project-copy">
            <p>DIANA erforscht, wie sich Such- und Empfehlungssysteme an die Ziele, Fähigkeiten und Wünsche einzelner Menschen anpassen lassen.</p>
            <p>Das Promotionsvorhaben verbindet die Erfassung persönlicher Angaben mit einem anpassbaren Matching und verständlichen Ergebnissen. Am Beispiel der Jobsuche untersucht es, wie diese Bereiche zusammenwirken und wie Nutzerinnen und Nutzer Empfehlungen im Dialog nachvollziehen und mitgestalten können.</p>
          </div>
          <div className="about-launch">
            <a href="/umfrage" className="about-start-link diana-action-motion"><span>Umfrage starten</span><span className="about-start-arrow diana-action-arrow" aria-hidden="true"><ArrowRight size={23} /></span></a>
          </div>
        </div>
      </section>
      </div>
      <section className="about-person" aria-labelledby="researcher-name">
        <img className="researcher-portrait" src={portrait} alt="Christoph Scharnagl" width="1122" height="1402" />
        <div className="researcher-copy">
          <span className="eyebrow">DER FORSCHER DAHINTER</span>
          <h2 id="researcher-name">Christoph Scharnagl <span>M. Sc.</span></h2>
          <p>Ich bin seit Januar 2025 wissenschaftlicher Mitarbeiter am Institut für Angewandte Informatik der Technischen Hochschule Nürnberg Georg Simon Ohm. Mein Forschungsschwerpunkt ist die Verbindung von Matching und natürlicher Sprachverarbeitung. Mit DIANA führe ich meine Forschung zum Abgleich von Lebensläufen und Stellenanzeigen fort.</p>
          <address className="researcher-contact">
            <a href="mailto:christoph.scharnagl@th-nuernberg.de">christoph.scharnagl@th-nuernberg.de</a>
            <span>Institut für Angewandte Informatik (IFAI)</span>
            <span>Keßlerstraße 1 · 90489 Nürnberg</span>
            <span>Sprechzeiten nach E-Mail-Vereinbarung</span>
          </address>
        </div>
      </section>
      <footer className="about-legal"><a href="/datenschutz">Datenschutz</a><a href="https://www.hochschuljobboerse.de/impressum" target="_blank" rel="noopener noreferrer">Impressum der Hochschuljobbörse</a></footer>
    </div>
  </main>;
}
