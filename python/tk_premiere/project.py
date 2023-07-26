# Copyright 2023 GPL Solutions, LLC.  All rights reserved.
#
# Use of this software is subject to the terms of the GPL Solutions license
# agreement provided at the time of installation or download, or which otherwise
# accompanies this software in either electronic or hard copy form.
#
from enum import IntEnum
import sgtk


class ItemType(IntEnum):
    """
    Mapping for Adobe ProjectItem types.
    """
    CLIP = 1  # A clip
    BIN = 2  # A bin
    ROOT = 3  # Root of the project
    FILE = 4  # A file


class PremiereItem(object):
    """
    Base class for objects handling Premiere objects.
    """
    def __init__(self, item):
        """
        Instantiate a new :class:`PremiereItem` from the given item.

        :param item: A Premiere object returned by the Adobe integration
                              as a :class:`ProxyWrapper`
        """
        super(PremiereItem, self).__init__()
        self._item = item

    @property
    def item(self):
        """
        Return the item associated with this instance.

        :returns: A Premiere ProjectItem.
        """
        return self._item

    @property
    def name(self):
        """
        """
        return self._item.name


class PremiereProject(PremiereItem):
    """
    A class to handle Premiere projects
    """

    @classmethod
    def get_current_project(cls):
        """
        Return the current Premiere project, if any.

        :returns: A :class:`PremiereProject`.
        :raises ValueError: If no current project can be found.
        """
        engine = sgtk.platform.current_engine()
        project = engine.adobe.app.project
        if not project:
            raise ValueError("No current Premiere project")

        return cls(project)

    def __init__(self, project):
        """
        Instantiate a new :class:`PremiereProject` for the given Premiere project.

        :param project: A Premiere project returned by the adobe integration
                        as a :class:`ProxyWrapper`
        """
        super(PremiereProject, self).__init__(project)

    @property
    def path(self):
        """
        """
        return self._item.path

    @property
    def bins(self):
        """

        """
        # The top project item is also a bin.
        bins = [self._item.rootItem]
        while bins:
            bin = bins.pop()
            # Iterating over childre directly sometimes
            # goes into infinite loops or returns ``None``
            # results, safer to iterate over the number
            # of children.
            for i in range(bin.children.numItems):
                child = bin.children[i]
                if child and child.type == ItemType.BIN:
                    bins.append(child)
            yield PremiereBin(bin)

    @property
    def clips(self):
        """
        """
        for bin in self.bins:
            for clip in bin.clips:
                yield clip

    @property
    def timelines(self):
        """
        Iterate over timelines for this project.

        :yields: :class:`PremiereTimeline`.
        """
        for sequence in self._item.sequences:
            yield PremiereTimeline(sequence)


class PremiereTimeline(PremiereItem):
    """
    A class to handle Premiere timelines (sequences).
    """

    def __init__(self, timeline):
        super(PremiereTimeline, self).__init__(timeline)


class PremiereBin(PremiereItem):
    """
    A class to handle Premiere bins.
    """
    def __init__(self, bin):
        super(PremiereBin, self).__init__(bin)

    @property
    def clips(self):
        """
        Iterate over all clips in this bin
        """
        # Iterating over childre directly sometimes
        # goes into infinite loops or returns ``None``
        # results, safer to iterate over the number
        # of children.
        for i in range(self._item.children.numItems):
            child = self._item.children[i]
            # Sequences are clips as well.
            if child.type == ItemType.CLIP and not child.isSequence():
                yield PremiereClip(child)

class PremiereClip(PremiereItem):
    """
    A class to handle Premiere clips.
    """
    def __init__(self, clip):
        super(PremiereClip, self).__init__(clip)

    @property
    def media_path(self):
        """
        Returns the media path associated with this clip.

        :returns: A string.
        """
        return self._item.getMediaPath()
