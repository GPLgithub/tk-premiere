# Copyright 2023 GPL Solutions, LLC.  All rights reserved.
#
# Use of this software is subject to the terms of the GPL Solutions license
# agreement provided at the time of installation or download, or which otherwise
# accompanies this software in either electronic or hard copy form.
#


class SessionInfo(object):
    """
    A class to retrieve informations from the current session.
    """

    def __init__(self, engine):
        """
        Instantiate a new SessionInfo.

        :param engine: A SG TK Engine.
        """
        self._engine = engine

    def get_transitions(self, transitions, timebase):
        """
        Return transitions details for the given list of transitions.

        :param transitions: A list of transitions.
        :returns: A list of dictionaries.
        """
        items = list()
        for i in transitions:
            item = dict(
                name=i.name,
                duration=i.duration.ticks / timebase,
                start=i.start.ticks / timebase,
                end=i.end.ticks / timebase,
                mediaType=i.mediaType,
                speed=i.getSpeed(),
            )
            items.append(item)
        return items

    def get_clip_items(self, clips, timebase):
        """
        Return the items for the given list of clips.

        :param clips: A list of clips.
        :param timebase: A timebase.
        :returns: A list of dictionaries.
        """
        # import sgtk
        # import os
        # engine = sgtk.platform.current_engine()
        items = list()

        for i in clips:

            getMediaPath_clip = i.projectItem.getMediaPath() if hasattr(i.projectItem, "getMediaPath") else None
            # canChangeMediaPath = i.projectItem.canChangeMediaPath() if hasattr(i.projectItem, 'canChangeMediaPath') else None

            item = dict(
                # shot_exists = shot_exists,
                name=i.name,
                duration=i.duration.ticks / timebase,
                start=i.start.ticks / timebase,
                end=i.end.ticks / timebase,
                inPoint=i.inPoint.ticks / timebase,
                outPoint=i.outPoint.ticks / timebase,
                mediaType=i.mediaType,
                # sym_link_entity=sym_link_entity,
                source_path_clip=getMediaPath_clip,
                # canChangeMediaPath = canChangeMediaPath,
                # videoComponents=videoComponents,
                isSelected=i.isSelected(),
                speed=i.getSpeed(),
                isAdjustmentLayer=i.isAdjustmentLayer()
            )

            items.append(item)

        return items

    def get_tracks(self, tracks, timebase):
        """
        Return details for the given list of tracks.

        :param tracks: A list of tracks.
        :param timebase: A timebase.
        :returns: A list of dictionaries.
        """
        tracks = list()
        for t in tracks:
            track = dict(
                id=t.id,
                name=t.name,
                mediaType=t.mediaType,
                clips=self.get_clip_items(t.clips, timebase),
                transitions=self.get_transitions(t.transitions, timebase),
                isMuted=t.isMuted()
            )
            tracks.append(track)
        return tracks

    def get_sequences(self, sequences):
        """
        Return details for the given list of sequences.

        :param sequences: A list of sequences.
        :returns: A list of dictionaries.
        """
        sequences = list()
        prj = self._engine.adobe.app.project
        active_seq = prj.activeSequence
        for s in sequences:
            # get info just for active sequence
            if s.name == active_seq.name:
                timebase = s.timebase
                sequence = dict(
                    sequenceID=s.sequenceID,
                    name=s.name,
                    inPoint=s.getInPointAsTime().ticks / timebase,
                    outPoint=s.getOutPointAsTime().ticks / timebase,
                    timebase=s.timebase,
                    zeroPoint=s.zeroPoint / timebase,
                    end=s.end / timebase,
                    videoTracks=self.get_tracks(s.videoTracks, timebase),
                    audioTracks=self.get_tracks(s.audioTracks, timebase)
                )
                sequences.append(sequence)
        return sequences

    def get_info(self):
        """
        Return information for the current session.

        :returns: A list of dictionaries.
        """
        session_info = list()
        for p in self._engine.adobe.app.projects:
            project = dict(
                documentID=p.documentID,
                name=p.name,
                path=p.path,
                sequences=self.get_sequences(p.sequences),
                activeSequence=p.activeSequence
            )
            session_info.append(project)
        return session_info
