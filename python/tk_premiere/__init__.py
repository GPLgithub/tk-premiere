# Copyright 2023 GPL Solutions, LLC.  All rights reserved.
#
# Use of this software is subject to the terms of the GPL Solutions license
# agreement provided at the time of installation or download, or which otherwise
# accompanies this software in either electronic or hard copy form.
#

import sys
import sgtk

from .session_info import SessionInfo
from .project import PremiereProject

adobe_bridge = sgtk.platform.import_framework(
    "tk-framework-adobe",
    "tk_framework_adobe.adobe_bridge"
)
AdobeBridge = adobe_bridge.AdobeBridge


shotgun_data = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_data")
shotgun_globals = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_globals")
shotgun_settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")


if sys.platform == "win32":
    win_32_api = sgtk.platform.import_framework(
        "tk-framework-adobe",
        "tk_framework_adobe_utils.win_32_api"
    )

