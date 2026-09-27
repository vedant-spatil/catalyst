import { useState } from "react";

type Props = { startOpen: boolean };

export default function PipelineGuide({ startOpen }: Props) {
  const [open, setOpen] = useState(startOpen);

  return (
    <>
    </>
    // <details
    //   className="guide"
    //   open={open}
    //   onToggle={(event) => setOpen(event.currentTarget.open)}
    // >
    //   <summary>How to add playlists and run the pipeline</summary>
    //   <p>
    //     The dashboard reads snapshots already in the warehouse. Add a playlist on the machine that runs the
    //     pipeline, then reload this page.
    //   </p>
    //   <ol>
    //     <li>
    //       From <code>backend/</code>, with the virtualenv active, list playlists on the Spotify account:
    //       <pre>python -m catalog_pipeline playlists</pre>
    //     </li>
    //     <li>
    //       Search for an artist and copy the id you want on the roster:
    //       <pre>python -m catalog_pipeline search --q &quot;artist name&quot;</pre>
    //     </li>
    //     <li>
    //       Put those ids in <code>seeds/watchlist.json</code>. <code>playlist_ids</code> are playlists this
    //       account owns or collaborates on.
    //     </li>
    //     <li>
    //       Pull a snapshot into the warehouse:
    //       <pre>python -m catalog_pipeline run</pre>
    //     </li>
    //     <li>Reload this page. Run the pipeline again on a later day to add another snapshot.</li>
    //   </ol>
    // </details>
  );
}
