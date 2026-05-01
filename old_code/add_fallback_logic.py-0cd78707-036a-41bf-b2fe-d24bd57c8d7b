"""Script to add fallback logic to Python files.

Script to add fallback logic to all Docker commands.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os


import re


import glob


def add_fallback_logic_to_file(file_path: str):
    """Add fallback logic to a Docker command file."""

    print(f"Processing {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if file already has fallback logic
    if "fallback from direct execution" in content:
        print(f"  ✅ Already has fallback logic")
        return False

    # Find the direct execution section
    direct_exec_pattern = r"# Direct execution without queue\\n\\n"

    fallback_pattern = r"# Direct execution without queue - try first, fallback to queue on error\\n            try:\\n"

    if direct_exec_pattern in content:
        # Replace the comment
        content = content.replace(direct_exec_pattern, fallback_pattern)

        # Find the end of direct execution and wrap it in try-except
        # Look for the return statement in direct execution
        return_pattern = r"(\\s+return \\{[^}]+\\})\\n\\n\\s+except docker\\.errors\\.DockerException as e:"

        def replace_return(match: re.Match[str]) -> str:  # type: ignore[name-defined]
            return_statement = match.group(1)
            template = """{return_statement}
                    
                except Exception as direct_error:
                    # If direct execution fails, automatically fallback to queue
                    self.logger.warning(f"Direct execution failed: {{direct_error}}. Falling back to queue.")
                    
                    from ai_admin.task_queue.queue_manager import queue_manager
                    from ai_admin.task_queue.task_queue import TaskType, Task
                    
                    # Determine task type based on command
                    task_type_map = {{
                    'docker_build': TaskType.DOCKER_BUILD,
                        'docker_pull': TaskType.DOCKER_PULL,
                        'docker_push': TaskType.DOCKER_PUSH,
                        'docker_run': TaskType.DOCKER_RUN,
                        'docker_stop': TaskType.DOCKER_STOP,
                        'docker_remove': TaskType.DOCKER_REMOVE,
                        'docker_tag': TaskType.DOCKER_TAG,
                    }}
                    
                    task_type = task_type_map.get(self.name, TaskType.DOCKER_RUN)
                    
                    # Add task to queue
                    task_id = await queue_manager.add_task(Task(
                        task_type=task_type,
                        params=kwargs
                    ))
                    
                    return {{
                    "message": f"{{self.name}} task queued successfully (fallback from direct execution)",
                        "task_id": task_id,
                        "use_queue": True,
                        "status": "queued",
                        "command": self.name,
                        "fallback_reason": str(direct_error),
                    }}
    
            except docker.errors.DockerException as e:"""
            return template.format(return_statement=return_statement)

        content = re.sub(return_pattern, replace_return, content, flags=re.DOTALL)

        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"  ✅ Added fallback logic")
        return True
    else:
        print(f"  ⚠️  No direct execution section found")
        return False


def main() -> None:
    """Main function to process all Docker command files."""
    print("Adding fallback logic to Docker commands...")

    # Find all Docker command files
    docker_files = glob.glob("ai_admin/commands/docker_*.py")

    processed = 0
    for file_path in docker_files:
        if add_fallback_logic_to_file(file_path):
            processed += 1

    print(f"\n✅ Processed {processed} files with fallback logic")
    # realusecmd verification


if __name__ == "__main__":
    main()


# CST realusecmd test - server-only workflow

# cst-node-ids: begin
# cst-node-ids: version=1
# cst-node-id 0 Module 2106e47e-e3a5-4e33-9eaf-2d57eaa80a2e
# cst-node-id 0.0 SimpleStatementLine 731049e5-02ac-4637-bc42-a1a5ecbdc9df
# cst-node-id 0.0.0 Expr 23f966cf-54c3-47b7-b46a-74a1fdea6704
# cst-node-id 0.0.0.0 SimpleString 189d44b9-0eb6-45cc-a60e-e7b566a46869
# cst-node-id 0.0.1 TrailingWhitespace 44400da8-d045-46f2-ad44-0ce7bd70258f
# cst-node-id 0.0.1.0 SimpleWhitespace a1f3dbe3-e4c0-43d1-8f86-a57c1170b130
# cst-node-id 0.0.1.1 Newline 3a719bde-98b1-4f8f-b8c9-efc0bc1a490a
# cst-node-id 0.1 SimpleStatementLine 35319a68-2d90-4b74-b42c-4283a1588971
# cst-node-id 0.1.0 EmptyLine fa072414-dac3-49d9-a254-81a9991265a8
# cst-node-id 0.1.0.0 SimpleWhitespace 9ae849f8-ab26-4d19-a4c4-c7225e3e5d1d
# cst-node-id 0.1.0.1 Newline 25e646cf-264c-4470-baeb-15c604edc98f
# cst-node-id 0.1.1 Import 2fdaac0b-53be-433c-a19a-105a06f28f6c
# cst-node-id 0.1.1.0 SimpleWhitespace f70e5a84-1825-46b3-9f98-fffd4972a77a
# cst-node-id 0.1.1.1 ImportAlias 24128794-e448-4257-b645-c791ce703384
# cst-node-id 0.1.1.1.0 Name 0e678216-4962-47b1-96ec-ccc7aea83108
# cst-node-id 0.1.2 TrailingWhitespace da209603-7072-4140-8c2f-01c4228bfb14
# cst-node-id 0.1.2.0 SimpleWhitespace a3920289-37e6-4b46-9508-d884f51d9d6c
# cst-node-id 0.1.2.1 Newline ed5df1f0-f3d9-49ed-89f8-fee108e4e972
# cst-node-id 0.2 SimpleStatementLine 4f471aa1-08d6-4996-a436-686863e76bd4
# cst-node-id 0.2.0 EmptyLine 56aa85f6-19e5-49aa-bd45-ab1fadbc28fc
# cst-node-id 0.2.0.0 SimpleWhitespace 7aed450b-15d8-4f93-8969-63962e080535
# cst-node-id 0.2.0.1 Newline 9ffa9360-5d61-4262-9900-a988c8bed4e1
# cst-node-id 0.2.1 EmptyLine 619e25fe-e5d8-4535-a435-34e8b1e784f0
# cst-node-id 0.2.1.0 SimpleWhitespace 0ef78705-f7ef-4be2-b6b1-dc1d4e361dc0
# cst-node-id 0.2.1.1 Newline 623b0a62-6031-4472-9e9a-578ec7e70343
# cst-node-id 0.2.2 Import fc9a0259-e811-4fba-bcd5-c2f828afdcac
# cst-node-id 0.2.2.0 SimpleWhitespace 789d4d62-b180-4751-b4e3-6d6d66e855be
# cst-node-id 0.2.2.1 ImportAlias 3a8651e1-eb00-4b21-9cee-d14a9f70533e
# cst-node-id 0.2.2.1.0 Name 3397b2c7-68cf-439f-a5ae-1fb616709f54
# cst-node-id 0.2.3 TrailingWhitespace b4d68800-af79-4361-a6ab-f2c10a8fd1d2
# cst-node-id 0.2.3.0 SimpleWhitespace 3f24153d-e5a6-46e5-b720-e1fa59d8d26a
# cst-node-id 0.2.3.1 Newline 7098ad64-5556-4925-a7fc-b1bd19144f82
# cst-node-id 0.3 SimpleStatementLine dd5ec8e3-68a0-4c64-9e62-a43a7bab3bb8
# cst-node-id 0.3.0 EmptyLine daa7c914-7fb1-4cc5-9d35-4ae09d3dcab9
# cst-node-id 0.3.0.0 SimpleWhitespace abbf594b-7e47-4b54-801b-abd197c42140
# cst-node-id 0.3.0.1 Newline 2d2cedf9-b0ef-4377-9734-26628f9a5ae6
# cst-node-id 0.3.1 EmptyLine 519abe4f-5dcd-46f5-8e29-422fa382674a
# cst-node-id 0.3.1.0 SimpleWhitespace 76ed4afc-fd15-48d7-a45f-c3cd6466106d
# cst-node-id 0.3.1.1 Newline 0690fe2a-beec-46bb-ab9e-7a5b38a8132a
# cst-node-id 0.3.2 Import 2330503d-190e-49eb-938f-43581aea077a
# cst-node-id 0.3.2.0 SimpleWhitespace 7b1aced2-e91d-4417-9557-983a8c3d8240
# cst-node-id 0.3.2.1 ImportAlias 6b39e559-3d1c-4910-be95-cfc62c968783
# cst-node-id 0.3.2.1.0 Name 38053711-77b9-47cf-9054-7c06628dc7e0
# cst-node-id 0.3.3 TrailingWhitespace 416455eb-def1-4dd0-8304-f05fcf8d8070
# cst-node-id 0.3.3.0 SimpleWhitespace e0f99953-7cda-4052-92bb-60d80a88b7e4
# cst-node-id 0.3.3.1 Newline 9ab97e84-96c1-488e-8eed-0bfe75dbecd2
# cst-node-id 0.4 FunctionDef 10addf4e-f3bb-43bc-8123-44c679d138b7
# cst-node-id 0.4.0 EmptyLine 3bb871e2-78a5-4153-8d36-f334254f1f12
# cst-node-id 0.4.0.0 SimpleWhitespace 8f7d1aa3-66be-45fb-ac34-f43853705408
# cst-node-id 0.4.0.1 Newline 67b68c71-a8ca-4bcc-b93b-0c357182ab2b
# cst-node-id 0.4.1 EmptyLine 8c89a954-e68b-4002-b517-39d2c1baf150
# cst-node-id 0.4.1.0 SimpleWhitespace 35ebdb1d-dd48-4275-9553-bb01b84dc0b8
# cst-node-id 0.4.1.1 Newline 3a428c66-184b-4a08-9f21-ac260bb0261e
# cst-node-id 0.4.2 SimpleWhitespace 9146f0ec-5902-4d30-9f0b-abb7d5c0b6dc
# cst-node-id 0.4.3 Name cc2a1042-6588-4ea9-8d3e-c91835cd2786
# cst-node-id 0.4.4 SimpleWhitespace 52fffbf2-48a6-4101-a3b3-7ad77f5c4ee0
# cst-node-id 0.4.5 SimpleWhitespace 2179be27-3b06-4051-933c-89983d7b3abf
# cst-node-id 0.4.6 SimpleWhitespace 8bec4dbc-4ddf-4be2-b366-e4484c9ed988
# cst-node-id 0.4.7 Parameters a79f8c80-e704-407d-987a-4fde34be4a94
# cst-node-id 0.4.7.0 Param ae3c075e-56b2-49f5-8aaf-51e8ab8d10bd
# cst-node-id 0.4.7.0.0 SimpleWhitespace ebc86275-6080-496c-ac0b-1770bbfef7f3
# cst-node-id 0.4.7.0.1 Name db5d3495-22d5-465f-ac85-a96e3209addc
# cst-node-id 0.4.7.0.2 Annotation 0b0abd4a-9183-47fb-bf8c-e36b5c282493
# cst-node-id 0.4.7.0.2.0 SimpleWhitespace fe07c109-8ba0-4e14-bbc3-7e3620071f11
# cst-node-id 0.4.7.0.2.1 SimpleWhitespace 8304382c-ee78-4458-8741-dfc180a81284
# cst-node-id 0.4.7.0.2.2 Name af1b54eb-2512-45f0-8bd6-186786d29d84
# cst-node-id 0.4.7.0.3 SimpleWhitespace 5decf4b1-7b73-465e-af48-d7d31c079c36
# cst-node-id 0.4.8 SimpleWhitespace fa1bea06-ea24-4b35-9ccd-62764bdd55cd
# cst-node-id 0.4.9 IndentedBlock 1862bbc6-a249-4a37-84cc-02db8a47f751
# cst-node-id 0.4.9.0 TrailingWhitespace 8c26dadc-20eb-4ed6-bde4-abcf160d504f
# cst-node-id 0.4.9.0.0 SimpleWhitespace db85965f-8b5b-4b7a-90d9-7b8138c8f0ee
# cst-node-id 0.4.9.0.1 Newline 8f17474d-40e9-4455-8773-d12c2bcbef90
# cst-node-id 0.4.9.1 SimpleStatementLine 0e37af77-c878-485b-a526-ff7fb81b1802
# cst-node-id 0.4.9.1.0 Expr 6e7bff74-0429-4745-85a3-9ac00c736953
# cst-node-id 0.4.9.1.0.0 SimpleString 889c6d52-d1ea-432b-a0d1-eb0057ed6135
# cst-node-id 0.4.9.1.1 TrailingWhitespace 1db9d237-ce70-4244-bcac-c3cf6f7bb988
# cst-node-id 0.4.9.1.1.0 SimpleWhitespace 6873f893-31ce-4f04-b8e9-aa2a929c26b9
# cst-node-id 0.4.9.1.1.1 Newline 20b3bd22-313b-4405-977c-bc12e3feb485
# cst-node-id 0.4.9.2 SimpleStatementLine 2ebd3806-e73e-46b4-a23b-41583924d82f
# cst-node-id 0.4.9.2.0 EmptyLine e7dbbd64-f9b3-469e-b819-508470fef90d
# cst-node-id 0.4.9.2.0.0 SimpleWhitespace 5238358e-1cbe-4ed6-aa12-d1a166090200
# cst-node-id 0.4.9.2.0.1 Newline 29b9a5a7-747a-4192-b050-ace3838f1f1c
# cst-node-id 0.4.9.2.1 Expr 31f3b938-97bd-4eb0-978d-86bfd7492be4
# cst-node-id 0.4.9.2.1.0 Call dd127496-612f-499e-9180-ab71369dc65d
# cst-node-id 0.4.9.2.1.0.0 Name 74717309-39e5-47e9-a74e-b049d01f013e
# cst-node-id 0.4.9.2.1.0.1 SimpleWhitespace f65ee8ab-2ad6-4271-9cb6-588502f148c1
# cst-node-id 0.4.9.2.1.0.2 SimpleWhitespace 7cef2317-755c-48ea-8b8e-8a3d31b15732
# cst-node-id 0.4.9.2.1.0.3 Arg c71026af-7fbf-4c49-9041-f23ab1ee2ad4
# cst-node-id 0.4.9.2.1.0.3.0 SimpleWhitespace 8ecc92ff-b9a8-494c-918a-1203e73860e3
# cst-node-id 0.4.9.2.1.0.3.1 FormattedString 6c8517c2-e7b8-415f-ac07-7619d107431d
# cst-node-id 0.4.9.2.1.0.3.1.0 FormattedStringText c60daa72-a9b9-4f8b-9ed8-c57537edf648
# cst-node-id 0.4.9.2.1.0.3.1.1 FormattedStringExpression 66b3c74c-30b1-4333-b721-681befde750c
# cst-node-id 0.4.9.2.1.0.3.1.1.0 SimpleWhitespace 75c8db6d-24ec-4db5-b02d-8ae861bd1f9b
# cst-node-id 0.4.9.2.1.0.3.1.1.1 Name 689bfc83-6802-4154-83a6-96a7986cda15
# cst-node-id 0.4.9.2.1.0.3.1.1.2 SimpleWhitespace 59893581-d63a-44d0-b96c-ca4ed9f205e5
# cst-node-id 0.4.9.2.1.0.3.1.2 FormattedStringText 972ef60e-f347-4ea7-9716-887381836147
# cst-node-id 0.4.9.2.1.0.3.2 SimpleWhitespace 3d622ba8-9910-4ffa-b06b-c71adb9f54a1
# cst-node-id 0.4.9.2.2 TrailingWhitespace 7fcc8f49-b74c-422f-a9a3-27535da066e8
# cst-node-id 0.4.9.2.2.0 SimpleWhitespace 162b9579-ce37-4a30-9e29-f1a8e9da7c58
# cst-node-id 0.4.9.2.2.1 Newline 37554817-4534-4606-bdf1-1595f1afe7c4
# cst-node-id 0.4.9.3 With ea57337d-5a3b-4312-8431-f239abe8ad40
# cst-node-id 0.4.9.3.0 EmptyLine 142a22e2-bcdb-47f6-a70e-d9362e4b18d4
# cst-node-id 0.4.9.3.0.0 SimpleWhitespace 5514e07e-88fa-4300-a7b3-8fa548fccd5f
# cst-node-id 0.4.9.3.0.1 Newline 07d4b615-a5f5-448c-8f6a-2088727c843f
# cst-node-id 0.4.9.3.1 SimpleWhitespace a3d3f622-35b0-4291-a23a-d1c466d0d22a
# cst-node-id 0.4.9.3.2 WithItem 284bc3ff-61dd-4bb4-9844-87876d9f4a97
# cst-node-id 0.4.9.3.2.0 Call efef5627-c4f6-4ed3-9e5f-b0cfb957624c
# cst-node-id 0.4.9.3.2.0.0 Name 610717a0-cef0-42e5-99e1-0fb321a23354
# cst-node-id 0.4.9.3.2.0.1 SimpleWhitespace d4fd3ce2-390d-43f2-82c5-66e06feae34e
# cst-node-id 0.4.9.3.2.0.2 SimpleWhitespace 8c6a81ae-399d-4e86-9cdc-b9dfc53b1ef9
# cst-node-id 0.4.9.3.2.0.3 Arg 084e3e2f-b431-4302-8755-fc669cbade42
# cst-node-id 0.4.9.3.2.0.3.0 SimpleWhitespace a36b6816-8010-49df-ad10-9ec3bd14dec8
# cst-node-id 0.4.9.3.2.0.3.1 Name 18249ea2-e3c8-423b-881c-bc155607a2f3
# cst-node-id 0.4.9.3.2.0.3.2 Comma e404992e-c144-445d-9671-99a26a9fcbc6
# cst-node-id 0.4.9.3.2.0.3.2.0 SimpleWhitespace b1cb7261-fccf-484b-9c0e-0be4c0639580
# cst-node-id 0.4.9.3.2.0.3.2.1 SimpleWhitespace 8ade1b08-612d-4090-ae35-b142d6a33fbc
# cst-node-id 0.4.9.3.2.0.3.3 SimpleWhitespace 1ca01006-5f12-440c-963a-3d1e4d05d5a6
# cst-node-id 0.4.9.3.2.0.4 Arg 83f7e07a-fe1b-4e66-b2d2-9c6d04172f72
# cst-node-id 0.4.9.3.2.0.4.0 SimpleWhitespace 27cac0a7-ec5f-4939-956f-57806947eb06
# cst-node-id 0.4.9.3.2.0.4.1 SimpleString 334c463a-4b07-4a9e-bfa7-bfd15f481fcd
# cst-node-id 0.4.9.3.2.0.4.2 Comma 48f97b65-9ec4-436e-bffa-2b17932f60fd
# cst-node-id 0.4.9.3.2.0.4.2.0 SimpleWhitespace 1ec229d8-4431-432e-acd3-e5c5bb4670f2
# cst-node-id 0.4.9.3.2.0.4.2.1 SimpleWhitespace 26b1895d-a1cb-46cd-8536-9d5b847b9296
# cst-node-id 0.4.9.3.2.0.4.3 SimpleWhitespace da24dd44-0a41-4c93-a29d-f04c0c3de81a
# cst-node-id 0.4.9.3.2.0.5 Arg 1ba65f6b-acbd-40c6-9252-1dbdc38702e3
# cst-node-id 0.4.9.3.2.0.5.0 SimpleWhitespace d4198e8e-d2fd-46dd-875e-44f70c27b497
# cst-node-id 0.4.9.3.2.0.5.1 Name d4be75dc-dc20-4da0-bdb4-1c33f79f5ffa
# cst-node-id 0.4.9.3.2.0.5.2 AssignEqual 2a88a357-80a6-4577-84b2-df09051803c8
# cst-node-id 0.4.9.3.2.0.5.2.0 SimpleWhitespace dffb948f-b8ea-4b7e-9490-fae0c0afdfd0
# cst-node-id 0.4.9.3.2.0.5.2.1 SimpleWhitespace 619d6d20-61b9-46d5-a9d0-fce9c2867284
# cst-node-id 0.4.9.3.2.0.5.3 SimpleString 0ffe05d6-1423-47bf-87db-a214667ca771
# cst-node-id 0.4.9.3.2.0.5.4 SimpleWhitespace 142decaf-ec60-4a34-9d3d-c3c4acf33a8e
# cst-node-id 0.4.9.3.2.1 AsName 71036196-7ba2-425c-8145-e296233b67a0
# cst-node-id 0.4.9.3.2.1.0 SimpleWhitespace a3cf7c3e-dbae-4c1d-8414-24d701881c41
# cst-node-id 0.4.9.3.2.1.1 Name 09db2c8b-c9c1-47b9-9a51-159874381449
# cst-node-id 0.4.9.3.2.1.2 SimpleWhitespace 78df8968-cfe3-4f10-a21c-4bf0e06f4793
# cst-node-id 0.4.9.3.3 SimpleWhitespace 886ea543-6545-4c07-8a75-ea5e8156e8c2
# cst-node-id 0.4.9.3.4 IndentedBlock 93a24c7a-2592-4454-a1d6-8081ff959a0a
# cst-node-id 0.4.9.3.4.0 TrailingWhitespace a951ef8d-bd97-4cf1-885e-d98a554b3614
# cst-node-id 0.4.9.3.4.0.0 SimpleWhitespace 79b3b36d-2d80-4ddb-b085-4f2c7530fd47
# cst-node-id 0.4.9.3.4.0.1 Newline f6d1c940-d002-4efe-a14f-51f3d29a0e22
# cst-node-id 0.4.9.3.4.1 SimpleStatementLine bdbb2a23-020b-4481-b550-d24971494de5
# cst-node-id 0.4.9.3.4.1.0 Assign fab714ec-3fa6-45a9-b9d2-adc641ca1e8c
# cst-node-id 0.4.9.3.4.1.0.0 AssignTarget de6ef316-c42a-4601-b1e7-ee548f13f562
# cst-node-id 0.4.9.3.4.1.0.0.0 Name e3c13d94-4fc5-4cb9-a1af-ea7835409185
# cst-node-id 0.4.9.3.4.1.0.0.1 SimpleWhitespace 033a7794-4df2-48ad-a015-fde7f09c91d6
# cst-node-id 0.4.9.3.4.1.0.0.2 SimpleWhitespace cbd3110d-a95b-4901-a165-5560addf694b
# cst-node-id 0.4.9.3.4.1.0.1 Call 1dad3528-0437-4723-8951-e7b6afab8de6
# cst-node-id 0.4.9.3.4.1.0.1.0 Attribute 06404160-a724-4118-9d8c-d41d33d42cbc
# cst-node-id 0.4.9.3.4.1.0.1.0.0 Name af344196-77af-47df-b0dd-8355c3f10c8f
# cst-node-id 0.4.9.3.4.1.0.1.0.1 Dot a177ec33-eaf1-4621-bb91-0390a22314a1
# cst-node-id 0.4.9.3.4.1.0.1.0.1.0 SimpleWhitespace 9571f5ec-1a2c-4ba9-bd44-3e9c0f2e166e
# cst-node-id 0.4.9.3.4.1.0.1.0.1.1 SimpleWhitespace 612c69a7-2089-44be-850f-99b9e4fe2491
# cst-node-id 0.4.9.3.4.1.0.1.0.2 Name 6232e9df-6c5e-479c-b334-a9bb61bd000c
# cst-node-id 0.4.9.3.4.1.0.1.1 SimpleWhitespace 6c4f84ee-7990-4ea2-883a-3148fbfa590e
# cst-node-id 0.4.9.3.4.1.0.1.2 SimpleWhitespace 5d08adbb-875a-4c2f-a13d-e8bb9a93b6b0
# cst-node-id 0.4.9.3.4.1.1 TrailingWhitespace 4639498a-56a1-431c-acd5-f1dd79e60cb8
# cst-node-id 0.4.9.3.4.1.1.0 SimpleWhitespace 1cb911ad-1df4-48c8-9d93-e19df2aa0a91
# cst-node-id 0.4.9.3.4.1.1.1 Newline 19ef6898-9406-482c-90d9-24e1c05e6d03
# cst-node-id 0.4.9.4 If 49a0e9e0-57d1-4c6c-a075-486ded45e993
# cst-node-id 0.4.9.4.0 EmptyLine a914bac3-ae53-4ec0-98be-43b61820e745
# cst-node-id 0.4.9.4.0.0 SimpleWhitespace a1511a1c-9ca2-4559-9ca7-d8e14ffdbcc3
# cst-node-id 0.4.9.4.0.1 Newline 1a4cfe23-4cef-45d5-825a-4767b99dc807
# cst-node-id 0.4.9.4.1 EmptyLine 9295eb90-1bdd-4500-aa69-3f127e78b713
# cst-node-id 0.4.9.4.1.0 SimpleWhitespace f872d03d-75c9-46ca-91c2-1840f72eade8
# cst-node-id 0.4.9.4.1.1 Comment 4c8fa738-6841-4e7d-9b96-031d842572d5
# cst-node-id 0.4.9.4.1.2 Newline a342afd4-6549-45b2-848d-25a8020f1815
# cst-node-id 0.4.9.4.2 SimpleWhitespace 88a5252d-0f63-495d-bda2-f38756124a89
# cst-node-id 0.4.9.4.3 Comparison 3e7e2c7e-d5c8-4255-8be4-523cf3419fd5
# cst-node-id 0.4.9.4.3.0 SimpleString 7402c33e-4951-4f6a-9ba5-7ca7b769d7c5
# cst-node-id 0.4.9.4.3.1 ComparisonTarget 4a63a06c-a885-46c0-bd4b-16a72f7d2a62
# cst-node-id 0.4.9.4.3.1.0 In 23e2aca9-2bb1-4aa9-bc2c-1401d904be71
# cst-node-id 0.4.9.4.3.1.0.0 SimpleWhitespace bccdc74c-5cd3-4d53-85c6-cf05782bf507
# cst-node-id 0.4.9.4.3.1.0.1 SimpleWhitespace d052ba21-d56a-495b-94c6-105b6016041f
# cst-node-id 0.4.9.4.3.1.1 Name 661b0392-6c21-4792-b77b-56b4fbea4c5a
# cst-node-id 0.4.9.4.4 SimpleWhitespace 5ac4108e-395c-4d3b-b1dc-1d9584a15b98
# cst-node-id 0.4.9.4.5 IndentedBlock 93af1ea0-ad39-437e-9c63-ec23e658b3be
# cst-node-id 0.4.9.4.5.0 TrailingWhitespace ad380d1d-e384-4d81-99b4-afc27937a6df
# cst-node-id 0.4.9.4.5.0.0 SimpleWhitespace 11fa6150-892c-4b8e-a0ef-f49f4446980d
# cst-node-id 0.4.9.4.5.0.1 Newline c31a6a40-d5f1-4892-8372-b78e5a216538
# cst-node-id 0.4.9.4.5.1 SimpleStatementLine 69ac013c-1d7e-4a4c-9211-da2922bda178
# cst-node-id 0.4.9.4.5.1.0 Expr 4821c3d0-4576-4533-b9fd-51489ba122bc
# cst-node-id 0.4.9.4.5.1.0.0 Call e0fbbdda-dfd8-4573-b55e-bc6c73dd4acf
# cst-node-id 0.4.9.4.5.1.0.0.0 Name 74a1224f-eb47-484d-89d1-22faeea41231
# cst-node-id 0.4.9.4.5.1.0.0.1 SimpleWhitespace a77d6b37-2bc5-4c23-a2df-ad9b6599f764
# cst-node-id 0.4.9.4.5.1.0.0.2 SimpleWhitespace 77b3d9b5-53c3-4404-94ec-c41ebc7f9d6d
# cst-node-id 0.4.9.4.5.1.0.0.3 Arg 1893035c-515d-4c2b-aa98-18037fc61859
# cst-node-id 0.4.9.4.5.1.0.0.3.0 SimpleWhitespace 0301c337-7d6f-4b0d-8d72-04d2d89c0d40
# cst-node-id 0.4.9.4.5.1.0.0.3.1 FormattedString 79ba1134-945e-419f-baeb-9d9e10456554
# cst-node-id 0.4.9.4.5.1.0.0.3.1.0 FormattedStringText 9b48bc11-9886-45d7-a8ad-c396627924af
# cst-node-id 0.4.9.4.5.1.0.0.3.2 SimpleWhitespace 8bb5b1da-9670-45dc-870b-b4475ca5b8f8
# cst-node-id 0.4.9.4.5.1.1 TrailingWhitespace 35f9bd34-1af9-4717-8571-297a66b41bd3
# cst-node-id 0.4.9.4.5.1.1.0 SimpleWhitespace fcaf388a-23b4-40b9-b51c-db8d4ae2680d
# cst-node-id 0.4.9.4.5.1.1.1 Newline c8d204e6-b2d9-4c74-9e4f-c00b51827bff
# cst-node-id 0.4.9.4.5.2 SimpleStatementLine 6f2ee6db-d546-4ef2-aa3d-044400abf544
# cst-node-id 0.4.9.4.5.2.0 Return 37f19cfd-8b14-47dd-a1bc-87f946866cc4
# cst-node-id 0.4.9.4.5.2.0.0 SimpleWhitespace ef3a69e5-4f5a-4bd6-a4e8-92b4aa1a03f6
# cst-node-id 0.4.9.4.5.2.0.1 Name 75be194a-a12e-4822-a2e6-9337e4e6ffe6
# cst-node-id 0.4.9.4.5.2.1 TrailingWhitespace fc87b8c1-e5c7-4196-85c4-c930983b34f7
# cst-node-id 0.4.9.4.5.2.1.0 SimpleWhitespace 27524c81-ab7a-4c7b-9932-58b6fdc07c17
# cst-node-id 0.4.9.4.5.2.1.1 Newline b1106ab1-4616-42af-8623-5228567786e1
# cst-node-id 0.4.9.5 SimpleStatementLine c7b85a15-a352-433e-b00b-03cca241a319
# cst-node-id 0.4.9.5.0 EmptyLine 91f4ff14-f6db-4f6a-9b2b-87314be8d25e
# cst-node-id 0.4.9.5.0.0 SimpleWhitespace 77f78947-2f29-4b6e-ad68-42fe94aed7e5
# cst-node-id 0.4.9.5.0.1 Newline 12717ab9-6fbc-4d5c-bb03-1f49f932b463
# cst-node-id 0.4.9.5.1 EmptyLine f8b39571-bea2-41f1-a187-585215ce63bb
# cst-node-id 0.4.9.5.1.0 SimpleWhitespace 74a0e79b-2687-4470-b3ce-fcace8a82444
# cst-node-id 0.4.9.5.1.1 Comment 37dab9a1-829f-4a4a-98f6-117302c6a24b
# cst-node-id 0.4.9.5.1.2 Newline b680c536-84dc-495c-9517-4fe540c3a7cc
# cst-node-id 0.4.9.5.2 Assign c57c08b8-b093-4a66-96cc-9dc7b0b35f5f
# cst-node-id 0.4.9.5.2.0 AssignTarget 1c4912f1-8886-46ab-ae31-2a4f85c1e9c9
# cst-node-id 0.4.9.5.2.0.0 Name a9825722-c544-4009-8071-51c58de769ad
# cst-node-id 0.4.9.5.2.0.1 SimpleWhitespace a31264ea-f44f-442a-9189-7e3f92331238
# cst-node-id 0.4.9.5.2.0.2 SimpleWhitespace 23189ec5-4d13-424d-bb68-ab97f85e2877
# cst-node-id 0.4.9.5.2.1 SimpleString 8148efbc-7768-4884-8c80-749cf6c8db2b
# cst-node-id 0.4.9.5.3 TrailingWhitespace 2232f35a-cb8c-45e6-882e-a1f5c0c64a78
# cst-node-id 0.4.9.5.3.0 SimpleWhitespace febc74c4-a99e-46ca-b462-2055230cf9e2
# cst-node-id 0.4.9.5.3.1 Newline f6b63d41-31b5-40b4-a3a1-a1ae704c12ef
# cst-node-id 0.4.9.6 SimpleStatementLine 1105fa92-5c86-4134-bcbc-0c6a79d7e322
# cst-node-id 0.4.9.6.0 EmptyLine 3bc4cd39-ae83-402e-8734-b0a19e0569b8
# cst-node-id 0.4.9.6.0.0 SimpleWhitespace 8605465b-53b1-4ba5-9837-d5a94c84c4b0
# cst-node-id 0.4.9.6.0.1 Newline 719952ec-ceb6-4774-b915-970cb41eca73
# cst-node-id 0.4.9.6.1 Assign a58a4de3-8d0b-40ab-aead-d74f9beaae08
# cst-node-id 0.4.9.6.1.0 AssignTarget 80f46913-85aa-48fb-8871-3041bb8f00df
# cst-node-id 0.4.9.6.1.0.0 Name 0a93d08f-f26f-4c16-9e51-1744c408b661
# cst-node-id 0.4.9.6.1.0.1 SimpleWhitespace d7f8f45a-e2c8-482e-90ab-6dedd2e66f11
# cst-node-id 0.4.9.6.1.0.2 SimpleWhitespace 2a6a6ab2-748f-46b8-812c-ed01acecba48
# cst-node-id 0.4.9.6.1.1 SimpleString a04cef60-b277-49a9-a221-284446d9075e
# cst-node-id 0.4.9.6.2 TrailingWhitespace b5d73957-355c-4bc8-9246-b016838935a0
# cst-node-id 0.4.9.6.2.0 SimpleWhitespace ba8fff4d-21ea-4afe-96bc-a6cb21ed49c5
# cst-node-id 0.4.9.6.2.1 Newline 8acefa87-36fc-46d0-a3a5-0d51aba2fe43
# cst-node-id 0.4.9.7 If d99e172c-d39d-4f21-83a6-c49cdb710cd2
# cst-node-id 0.4.9.7.0 EmptyLine b983f82b-3881-4c24-b47d-71366677e6ee
# cst-node-id 0.4.9.7.0.0 SimpleWhitespace b1edea1e-8857-4dd4-8db7-998a597c5110
# cst-node-id 0.4.9.7.0.1 Newline cf17ef86-0ec8-4916-972a-43b0000962a5
# cst-node-id 0.4.9.7.1 SimpleWhitespace a68d3efc-2fc2-4f50-9257-fed88b46ceb6
# cst-node-id 0.4.9.7.2 Comparison 6ef45673-3687-4aea-8e0a-f824e165944b
# cst-node-id 0.4.9.7.2.0 Name 38d0cf53-aa16-4f0e-94f2-8a4a9a3976b5
# cst-node-id 0.4.9.7.2.1 ComparisonTarget 740c9897-0e63-468c-857a-2e3d8293e7d9
# cst-node-id 0.4.9.7.2.1.0 In b8f5d5cf-1afc-498a-b825-03004d407ec7
# cst-node-id 0.4.9.7.2.1.0.0 SimpleWhitespace ec957c54-ad0f-489a-b364-857bbb0f5548
# cst-node-id 0.4.9.7.2.1.0.1 SimpleWhitespace 9843d940-11bb-4683-bcbd-21c192e4fc21
# cst-node-id 0.4.9.7.2.1.1 Name 5c6734d3-fbac-4cc1-bce6-f760ae8323ea
# cst-node-id 0.4.9.7.3 SimpleWhitespace 6e617b2b-31f4-49f4-9c2e-b411611c33c4
# cst-node-id 0.4.9.7.4 IndentedBlock 007f4fdc-038a-4c5b-9d11-c8ee48e64444
# cst-node-id 0.4.9.7.4.0 TrailingWhitespace 67f6f611-a682-4a5b-9d97-4dce4680df8e
# cst-node-id 0.4.9.7.4.0.0 SimpleWhitespace 4acbc7a3-489e-4af6-98b9-5588ca304646
# cst-node-id 0.4.9.7.4.0.1 Newline 205a7260-8ebd-4ef5-b567-870a67147deb
# cst-node-id 0.4.9.7.4.1 SimpleStatementLine d4e5b727-ed7a-4dc4-bb3d-540815771134
# cst-node-id 0.4.9.7.4.1.0 EmptyLine 061c8361-6283-48e2-873a-4d625dcd090f
# cst-node-id 0.4.9.7.4.1.0.0 SimpleWhitespace ef2615d9-368c-497e-8d8e-af55d2c916f6
# cst-node-id 0.4.9.7.4.1.0.1 Comment 18aa9e19-12a6-4f26-b90a-fc6d29dac735
# cst-node-id 0.4.9.7.4.1.0.2 Newline b2a16a5f-81a1-4122-b2ec-0763ef410b05
# cst-node-id 0.4.9.7.4.1.1 Assign e9c591b7-68e5-4e0c-9d45-2a35074887cf
# cst-node-id 0.4.9.7.4.1.1.0 AssignTarget 0d242376-1e8d-4d8e-ac92-2f8526ffcac3
# cst-node-id 0.4.9.7.4.1.1.0.0 Name 7727ef4e-daf3-4fbb-943b-1bd0e49efc0c
# cst-node-id 0.4.9.7.4.1.1.0.1 SimpleWhitespace a67e5ec4-196c-4492-91f7-6bcb05ea856c
# cst-node-id 0.4.9.7.4.1.1.0.2 SimpleWhitespace c8b5c79f-a63d-4c2b-a12c-0310904986f1
# cst-node-id 0.4.9.7.4.1.1.1 Call 581ac22c-8bd7-4a8e-9554-61e33cdf4063
# cst-node-id 0.4.9.7.4.1.1.1.0 Attribute c39aba64-464e-4928-bbf1-36e8b07510bc
# cst-node-id 0.4.9.7.4.1.1.1.0.0 Name 989e89a8-888b-443c-b711-6550b6f69982
# cst-node-id 0.4.9.7.4.1.1.1.0.1 Dot eb4dcc27-88ff-471d-8632-555077d1ee4d
# cst-node-id 0.4.9.7.4.1.1.1.0.1.0 SimpleWhitespace d862d218-9c88-4cc2-989d-4f93ff7d5ec9
# cst-node-id 0.4.9.7.4.1.1.1.0.1.1 SimpleWhitespace 35ae70dd-bcf1-4e63-b8a7-d67292d531d4
# cst-node-id 0.4.9.7.4.1.1.1.0.2 Name f028d719-a911-47d3-8cc9-6c07e1a9545c
# cst-node-id 0.4.9.7.4.1.1.1.1 SimpleWhitespace b2eedd14-1661-43df-8126-74e3aae33dce
# cst-node-id 0.4.9.7.4.1.1.1.2 SimpleWhitespace 3f396360-32dd-4409-8565-7c6b871c3772
# cst-node-id 0.4.9.7.4.1.1.1.3 Arg 4857f819-4e5d-465d-96d0-224835a5980d
# cst-node-id 0.4.9.7.4.1.1.1.3.0 SimpleWhitespace e342cbf3-2adc-49ad-9655-8345c3c968b0
# cst-node-id 0.4.9.7.4.1.1.1.3.1 Name 489a513e-8194-41ee-a36b-065d6e9e69f2
# cst-node-id 0.4.9.7.4.1.1.1.3.2 Comma 95ff7e58-1fe3-45a8-be5c-33c6b0c0422f
# cst-node-id 0.4.9.7.4.1.1.1.3.2.0 SimpleWhitespace 50c76293-ff69-4420-aef0-e3afd8c374fe
# cst-node-id 0.4.9.7.4.1.1.1.3.2.1 SimpleWhitespace ef18ad21-e4f9-4c28-a9fd-f2a7b4a542d1
# cst-node-id 0.4.9.7.4.1.1.1.3.3 SimpleWhitespace 2c5107c7-8d80-460f-baa4-633c3d7abe30
# cst-node-id 0.4.9.7.4.1.1.1.4 Arg f11b697f-ed71-4783-b406-8970fb2f7ef9
# cst-node-id 0.4.9.7.4.1.1.1.4.0 SimpleWhitespace f38a2cf2-2c23-4219-84cf-edc18657cca8
# cst-node-id 0.4.9.7.4.1.1.1.4.1 Name d0211dff-0f92-4da0-bd72-a61805091b28
# cst-node-id 0.4.9.7.4.1.1.1.4.2 SimpleWhitespace 7e0e3b85-9dcf-4842-9f2a-fcfe37137d52
# cst-node-id 0.4.9.7.4.1.2 TrailingWhitespace 88d6d8b1-6fc9-46e2-a799-1e1efdb2af41
# cst-node-id 0.4.9.7.4.1.2.0 SimpleWhitespace 6d2de865-bcb1-4487-bb4c-fa9b815179e4
# cst-node-id 0.4.9.7.4.1.2.1 Newline c3ada584-51e2-4ccf-b4df-7b91093d4413
# cst-node-id 0.4.9.7.4.2 SimpleStatementLine cf3d0d62-2ecc-469e-8e32-8415d9a26a47
# cst-node-id 0.4.9.7.4.2.0 EmptyLine 8f7bf288-c132-4f88-89aa-cad9ca4b4d09
# cst-node-id 0.4.9.7.4.2.0.0 SimpleWhitespace 8277b0ca-0267-455f-88f0-467fdade188e
# cst-node-id 0.4.9.7.4.2.0.1 Newline e141d7d3-08ec-43ba-8283-bcb2d035bf4f
# cst-node-id 0.4.9.7.4.2.1 EmptyLine 7761427f-0051-441b-a1d6-0eb6b4692f2f
# cst-node-id 0.4.9.7.4.2.1.0 SimpleWhitespace 90d09798-44e2-41e4-8265-551a35d44ef6
# cst-node-id 0.4.9.7.4.2.1.1 Comment 35e3c450-af0c-42a3-ac5f-bbaab0132a96
# cst-node-id 0.4.9.7.4.2.1.2 Newline 7bcf13dd-1351-4546-aecd-b8da9752ea04
# cst-node-id 0.4.9.7.4.2.2 EmptyLine 18883abd-d270-4b0e-8c6e-37b367806377
# cst-node-id 0.4.9.7.4.2.2.0 SimpleWhitespace 14083e78-0365-45c2-a215-c3ebf42cdd05
# cst-node-id 0.4.9.7.4.2.2.1 Comment cde13e20-3ab3-45a9-bee9-d19be4fe9934
# cst-node-id 0.4.9.7.4.2.2.2 Newline d2f1f96a-53e2-43e2-9521-6375336481a2
# cst-node-id 0.4.9.7.4.2.3 Assign 5293a23c-a988-4e43-afa3-6de5d9e281f4
# cst-node-id 0.4.9.7.4.2.3.0 AssignTarget 7131ed0a-3413-4179-a900-c2530d511bda
# cst-node-id 0.4.9.7.4.2.3.0.0 Name 6875308b-a0bf-4967-953c-5a0555a88c90
# cst-node-id 0.4.9.7.4.2.3.0.1 SimpleWhitespace 7cb69ca9-cf70-4dcb-931b-ef1fae0a1e7c
# cst-node-id 0.4.9.7.4.2.3.0.2 SimpleWhitespace f93db78a-2b6e-4a84-84aa-dd0995e5d4bd
# cst-node-id 0.4.9.7.4.2.3.1 SimpleString 079afc15-fd9c-4140-ab87-cca5961dab49
# cst-node-id 0.4.9.7.4.2.4 TrailingWhitespace 2fa89a30-da2c-4fac-9f48-3877063066c4
# cst-node-id 0.4.9.7.4.2.4.0 SimpleWhitespace ca8b153e-0635-4f9a-adee-b6a753459b0e
# cst-node-id 0.4.9.7.4.2.4.1 Newline 9d1e4643-f2cf-419b-b06a-e361eeb5c97a
# cst-node-id 0.4.9.7.4.3 FunctionDef 8c40ec60-3917-4547-982e-07e8d27657e3
# cst-node-id 0.4.9.7.4.3.0 EmptyLine 814ded27-9c12-4f18-8659-6792867e602f
# cst-node-id 0.4.9.7.4.3.0.0 SimpleWhitespace 1456b0a5-f375-4445-83e3-c9735624ed6e
# cst-node-id 0.4.9.7.4.3.0.1 Newline 14c93339-fb94-45d9-ba3f-e2ced535f932
# cst-node-id 0.4.9.7.4.3.1 SimpleWhitespace a28fa451-5e0b-4def-b5c3-dcc1050240d3
# cst-node-id 0.4.9.7.4.3.2 Name 3dce7195-1ace-4eab-af42-f9077cdc69df
# cst-node-id 0.4.9.7.4.3.3 SimpleWhitespace 6a65ead1-81b8-426f-818f-f848f8b610d8
# cst-node-id 0.4.9.7.4.3.4 SimpleWhitespace 2e85787d-57c0-4573-9f9f-e76ea58dee3d
# cst-node-id 0.4.9.7.4.3.5 SimpleWhitespace 56d40ad2-531d-4aa5-a867-740d9d2acc3e
# cst-node-id 0.4.9.7.4.3.6 Parameters 07ad8d81-77a3-46b3-8613-1c7c3c0d0a66
# cst-node-id 0.4.9.7.4.3.6.0 Param b0b5e080-e312-4105-964c-5f0e2178d2f6
# cst-node-id 0.4.9.7.4.3.6.0.0 SimpleWhitespace e0df05a0-f5a4-4b5b-aa12-5a31dc6fdab1
# cst-node-id 0.4.9.7.4.3.6.0.1 Name 008009b1-354e-4b38-ad85-70679fa64908
# cst-node-id 0.4.9.7.4.3.6.0.2 Annotation 18517ddb-039f-418c-bf03-dc74c9132fa1
# cst-node-id 0.4.9.7.4.3.6.0.2.0 SimpleWhitespace 21396fad-7e77-4e3d-ade0-d9eeadb62709
# cst-node-id 0.4.9.7.4.3.6.0.2.1 SimpleWhitespace ad722649-008d-4fcb-9a9a-eb110baecefe
# cst-node-id 0.4.9.7.4.3.6.0.2.2 Subscript 4c4e2a45-4a4e-43a5-a894-ab2a94b64b68
# cst-node-id 0.4.9.7.4.3.6.0.2.2.0 Attribute c0940b15-ebc4-43ac-90b5-5e6bf51350e4
# cst-node-id 0.4.9.7.4.3.6.0.2.2.0.0 Name 4528787e-006f-4322-a16c-18ae96f3217f
# cst-node-id 0.4.9.7.4.3.6.0.2.2.0.1 Dot 61ef8b7b-9b4a-4556-936c-1f15f31f565d
# cst-node-id 0.4.9.7.4.3.6.0.2.2.0.1.0 SimpleWhitespace 52aace2e-089e-49e3-970e-19dc10879b0f
# cst-node-id 0.4.9.7.4.3.6.0.2.2.0.1.1 SimpleWhitespace 45209914-555d-4d05-8532-2395207363b6
# cst-node-id 0.4.9.7.4.3.6.0.2.2.0.2 Name a65ece74-d33b-40e9-af9b-78784c433be5
# cst-node-id 0.4.9.7.4.3.6.0.2.2.1 SimpleWhitespace f4545a93-1554-4494-a08f-1036ee623407
# cst-node-id 0.4.9.7.4.3.6.0.2.2.2 LeftSquareBracket 1daef7a4-73d3-42a4-af4c-7135de0a930a
# cst-node-id 0.4.9.7.4.3.6.0.2.2.2.0 SimpleWhitespace f5121a22-78b7-4c11-b1b7-763240138aac
# cst-node-id 0.4.9.7.4.3.6.0.2.2.3 SubscriptElement 2ded0fa1-98d6-40cf-9597-9aa3f2f3cdda
# cst-node-id 0.4.9.7.4.3.6.0.2.2.3.0 Index 6c55dbf1-0098-45d0-9fdd-18f633a2575f
# cst-node-id 0.4.9.7.4.3.6.0.2.2.3.0.0 Name 649ee04b-e946-46fb-b3bc-ce4294a0c210
# cst-node-id 0.4.9.7.4.3.6.0.2.2.4 RightSquareBracket ed650c12-edde-4ebd-9803-789468c19060
# cst-node-id 0.4.9.7.4.3.6.0.2.2.4.0 SimpleWhitespace a342d609-ada1-45d2-8d38-e96b9edcd17f
# cst-node-id 0.4.9.7.4.3.6.0.3 SimpleWhitespace b5fcd709-0138-4035-aafd-3313a64c6b62
# cst-node-id 0.4.9.7.4.3.7 Annotation 599bf75e-ca9c-467d-b90c-ce9636fc9c1f
# cst-node-id 0.4.9.7.4.3.7.0 SimpleWhitespace 67f16519-9fa2-4181-a724-4846ab2139ea
# cst-node-id 0.4.9.7.4.3.7.1 SimpleWhitespace d127760d-6919-4595-80f9-21b563e04593
# cst-node-id 0.4.9.7.4.3.7.2 Name fcd0b19f-9ab8-41b3-98a5-84717593e5fd
# cst-node-id 0.4.9.7.4.3.8 SimpleWhitespace cf245018-304f-489f-bfbe-eeab7aec6cf3
# cst-node-id 0.4.9.7.4.3.9 IndentedBlock f5ca41e0-2543-4491-a4b4-f0fabdc252f9
# cst-node-id 0.4.9.7.4.3.9.0 TrailingWhitespace fc23637c-2ffe-40b4-b721-0e611485623c
# cst-node-id 0.4.9.7.4.3.9.0.0 SimpleWhitespace b73bb2fe-8f41-4203-937b-7ba41dd1ed12
# cst-node-id 0.4.9.7.4.3.9.0.1 Comment 5d3ef3c0-160a-4c4a-97d1-8a9d57a1cabc
# cst-node-id 0.4.9.7.4.3.9.0.2 Newline dcbe1c35-1695-4a84-afce-463658123954
# cst-node-id 0.4.9.7.4.3.9.1 SimpleStatementLine 3ab9f193-a157-4edc-9271-bd14b75fa7b5
# cst-node-id 0.4.9.7.4.3.9.1.0 Assign c7ae1a4b-de1e-46ee-81cc-47d3942a816c
# cst-node-id 0.4.9.7.4.3.9.1.0.0 AssignTarget c48e3e2d-38f3-4c36-aec8-df814ed0c95f
# cst-node-id 0.4.9.7.4.3.9.1.0.0.0 Name a0d0886e-eb34-47f5-943b-685261cac9c8
# cst-node-id 0.4.9.7.4.3.9.1.0.0.1 SimpleWhitespace 400339db-13b6-4997-9dc2-01d4ff6d0588
# cst-node-id 0.4.9.7.4.3.9.1.0.0.2 SimpleWhitespace 79e62a04-2505-42cf-937b-55eb9f069009
# cst-node-id 0.4.9.7.4.3.9.1.0.1 Call 7b278114-aa18-4444-b950-004b5a24fb6d
# cst-node-id 0.4.9.7.4.3.9.1.0.1.0 Attribute 56938dd3-0856-4119-b11d-282ccb6332ca
# cst-node-id 0.4.9.7.4.3.9.1.0.1.0.0 Name d132457d-d7c5-4996-82bd-1965fd4e4492
# cst-node-id 0.4.9.7.4.3.9.1.0.1.0.1 Dot e50a9b95-de62-468d-95a8-7a04a2b23381
# cst-node-id 0.4.9.7.4.3.9.1.0.1.0.1.0 SimpleWhitespace 3bded715-ec27-422e-becf-73d9796c716e
# cst-node-id 0.4.9.7.4.3.9.1.0.1.0.1.1 SimpleWhitespace a1bb5f25-1ff4-44da-9adf-7b6bd8546324
# cst-node-id 0.4.9.7.4.3.9.1.0.1.0.2 Name ffe1ceed-2d13-4693-8be5-62f7c88ba33f
# cst-node-id 0.4.9.7.4.3.9.1.0.1.1 SimpleWhitespace 5e66c1d6-184a-426c-86e2-8d6e655fe38c
# cst-node-id 0.4.9.7.4.3.9.1.0.1.2 SimpleWhitespace 281b92dd-e7e1-479a-a40a-2d4dfdf32910
# cst-node-id 0.4.9.7.4.3.9.1.0.1.3 Arg 80781603-b77b-4b3c-a024-73dcab4cf77a
# cst-node-id 0.4.9.7.4.3.9.1.0.1.3.0 SimpleWhitespace 51af7890-ad67-437b-bce1-9460f1c20a10
# cst-node-id 0.4.9.7.4.3.9.1.0.1.3.1 Integer 65c33c4e-ad7f-4d6d-b88d-a59ea920d0b4
# cst-node-id 0.4.9.7.4.3.9.1.0.1.3.2 SimpleWhitespace 3cd3ff33-8fb5-4fc8-a0ec-2cc51fcb7a63
# cst-node-id 0.4.9.7.4.3.9.1.1 TrailingWhitespace 81d8dafd-376a-4ef0-aaca-a408518765e4
# cst-node-id 0.4.9.7.4.3.9.1.1.0 SimpleWhitespace 74dc2cbb-6d37-453b-bb47-96eb689be617
# cst-node-id 0.4.9.7.4.3.9.1.1.1 Newline f19f93d6-8e25-4791-84dc-1679e928ed8e
# cst-node-id 0.4.9.7.4.3.9.2 SimpleStatementLine d74dae8e-10ac-46bd-8d99-527cecdd4f3c
# cst-node-id 0.4.9.7.4.3.9.2.0 Assign 17957569-4ce7-4da6-b630-ce661284fa46
# cst-node-id 0.4.9.7.4.3.9.2.0.0 AssignTarget f7dcc6bc-c7bd-401d-b0df-5c0225a8f321
# cst-node-id 0.4.9.7.4.3.9.2.0.0.0 Name 2b53f892-f732-4f6d-b5c0-40e7b8e61f7e
# cst-node-id 0.4.9.7.4.3.9.2.0.0.1 SimpleWhitespace c9eff38d-2eeb-4c8b-b2ad-84e0e706f2bd
# cst-node-id 0.4.9.7.4.3.9.2.0.0.2 SimpleWhitespace a8faa757-4eab-4a02-8e76-96e2741fc96e
# cst-node-id 0.4.9.7.4.3.9.2.0.1 SimpleString 1ee5932d-ca5d-40c5-83b1-596b5d91d5fc
# cst-node-id 0.4.9.7.4.3.9.2.1 TrailingWhitespace 60a2fb7b-fae9-4a43-9592-f38dd2fa6418
# cst-node-id 0.4.9.7.4.3.9.2.1.0 SimpleWhitespace 7b402f2f-a52b-4460-8b15-5cf88f765a46
# cst-node-id 0.4.9.7.4.3.9.2.1.1 Newline f665d1dc-5138-4106-b8e5-351f44b3a3d1
# cst-node-id 0.4.9.7.4.3.9.3 SimpleStatementLine fddd8bec-c097-4f38-8c0c-5e54de16111d
# cst-node-id 0.4.9.7.4.3.9.3.0 Return e5b45ed7-4174-4a8e-9b8e-eedf21e13149
# cst-node-id 0.4.9.7.4.3.9.3.0.0 SimpleWhitespace 99611230-feb1-4e5f-be91-3cb36eb4ac1b
# cst-node-id 0.4.9.7.4.3.9.3.0.1 Call 6d56cacd-36a2-42ee-8984-9081c79d7b3f
# cst-node-id 0.4.9.7.4.3.9.3.0.1.0 Attribute 718f6a65-9a7c-4b1a-9ebe-0506d20c6aa2
# cst-node-id 0.4.9.7.4.3.9.3.0.1.0.0 Name cd94c63b-5ac9-4231-8ae6-af2529edf9e6
# cst-node-id 0.4.9.7.4.3.9.3.0.1.0.1 Dot 7bae0b81-482a-4f50-8244-74b5596a6879
# cst-node-id 0.4.9.7.4.3.9.3.0.1.0.1.0 SimpleWhitespace a5c6a111-b560-4a91-bd4e-f330f432060e
# cst-node-id 0.4.9.7.4.3.9.3.0.1.0.1.1 SimpleWhitespace e6e0fd94-498d-4828-b5aa-daf773882384
# cst-node-id 0.4.9.7.4.3.9.3.0.1.0.2 Name 5ed1fca9-40d3-4c37-912b-431c4e3c6b13
# cst-node-id 0.4.9.7.4.3.9.3.0.1.1 SimpleWhitespace 10a1dca6-fec0-4db6-b770-5311f74c966c
# cst-node-id 0.4.9.7.4.3.9.3.0.1.2 SimpleWhitespace 2ed45d70-25c0-47d2-b288-4f2fc9678722
# cst-node-id 0.4.9.7.4.3.9.3.0.1.3 Arg 44a351b3-2be6-4829-9e49-e5a1586ee677
# cst-node-id 0.4.9.7.4.3.9.3.0.1.3.0 SimpleWhitespace 460c79c2-1869-4577-a109-ca565198d7b2
# cst-node-id 0.4.9.7.4.3.9.3.0.1.3.1 Name 8c142616-15bf-4ab1-84d2-f8d92affc21c
# cst-node-id 0.4.9.7.4.3.9.3.0.1.3.2 AssignEqual ac504028-d21e-4f16-9b2b-471d937b3918
# cst-node-id 0.4.9.7.4.3.9.3.0.1.3.2.0 SimpleWhitespace 4b34fc52-07ef-4ffc-9a4c-1ddc09849951
# cst-node-id 0.4.9.7.4.3.9.3.0.1.3.2.1 SimpleWhitespace 9eb75962-e752-47ee-a690-5425433ae7d1
# cst-node-id 0.4.9.7.4.3.9.3.0.1.3.3 Name 05789356-fac2-4b41-bb3f-fc292b21590e
# cst-node-id 0.4.9.7.4.3.9.3.0.1.3.4 SimpleWhitespace 369e6f4a-a82c-4323-ab8a-fef78463d416
# cst-node-id 0.4.9.7.4.3.9.3.1 TrailingWhitespace 92bce57d-6885-43d0-bfcf-18771bf494fb
# cst-node-id 0.4.9.7.4.3.9.3.1.0 SimpleWhitespace 7407f2b0-1016-4652-87ea-43ab019beee5
# cst-node-id 0.4.9.7.4.3.9.3.1.1 Newline 76438d00-9451-4133-9f67-1d2e58f6dfb6
# cst-node-id 0.4.9.7.4.4 SimpleStatementLine 8415c230-9b93-45b4-9dab-72fbaff0b9f4
# cst-node-id 0.4.9.7.4.4.0 EmptyLine 302f8679-787b-4ae3-8211-4ed11dbd984a
# cst-node-id 0.4.9.7.4.4.0.0 SimpleWhitespace d6877c3e-d4ad-47fd-9615-6ef56c0fbefa
# cst-node-id 0.4.9.7.4.4.0.1 Newline ee732a22-5fe5-40e6-a451-793449bf6e9e
# cst-node-id 0.4.9.7.4.4.1 Assign 29394e24-eb26-4ec8-ac87-0bccadc03302
# cst-node-id 0.4.9.7.4.4.1.0 AssignTarget e4c1ff9a-936f-4ccd-9265-eb8f0f92cf6e
# cst-node-id 0.4.9.7.4.4.1.0.0 Name b7970469-faea-4d23-94e9-8aad248d80ab
# cst-node-id 0.4.9.7.4.4.1.0.1 SimpleWhitespace 893dfa31-5a79-4482-9dc7-db95dba4d8e2
# cst-node-id 0.4.9.7.4.4.1.0.2 SimpleWhitespace 72f708ee-6bbc-4807-9fca-b3f9db22cebc
# cst-node-id 0.4.9.7.4.4.1.1 Call 6392d38f-267b-4afe-b135-19f8dab29c90
# cst-node-id 0.4.9.7.4.4.1.1.0 Attribute 20880ab4-f3ea-49d0-8587-6df865ff4d53
# cst-node-id 0.4.9.7.4.4.1.1.0.0 Name 54ec82d6-0466-4c4e-bdf7-d355666b8bc3
# cst-node-id 0.4.9.7.4.4.1.1.0.1 Dot dfb4bfb8-31f1-4e99-b986-1726b08996d9
# cst-node-id 0.4.9.7.4.4.1.1.0.1.0 SimpleWhitespace 80bb5b46-279c-4cb1-a1b1-82a9f392aaeb
# cst-node-id 0.4.9.7.4.4.1.1.0.1.1 SimpleWhitespace 21a1ebac-fce5-4632-8eaf-019edba65fa4
# cst-node-id 0.4.9.7.4.4.1.1.0.2 Name 2794957e-9224-4a54-9762-7739e2fc02bf
# cst-node-id 0.4.9.7.4.4.1.1.1 SimpleWhitespace b0673600-0513-4ac8-85ad-f28c4c29697b
# cst-node-id 0.4.9.7.4.4.1.1.2 SimpleWhitespace 2bf3cef9-cab7-45f2-a7cd-7c025f194b5d
# cst-node-id 0.4.9.7.4.4.1.1.3 Arg 4f066648-2173-45fb-917e-baedaae7b3d6
# cst-node-id 0.4.9.7.4.4.1.1.3.0 SimpleWhitespace 31dbc35c-be03-4043-9838-37c32ee76d8d
# cst-node-id 0.4.9.7.4.4.1.1.3.1 Name 4599c1f1-ac40-45fb-88c2-4b857b74c686
# cst-node-id 0.4.9.7.4.4.1.1.3.2 Comma 914713bc-9761-448b-933d-907a4a8316b4
# cst-node-id 0.4.9.7.4.4.1.1.3.2.0 SimpleWhitespace 0e301c39-5e0f-47e9-b82b-d8071717da56
# cst-node-id 0.4.9.7.4.4.1.1.3.2.1 SimpleWhitespace 46fe50b8-5988-43ad-8b01-a6afddad2c4b
# cst-node-id 0.4.9.7.4.4.1.1.3.3 SimpleWhitespace 2ceb4152-d6a0-41b9-abe5-0aef2971f4a8
# cst-node-id 0.4.9.7.4.4.1.1.4 Arg 95d519c5-9b72-4442-9594-07f8f1ac404b
# cst-node-id 0.4.9.7.4.4.1.1.4.0 SimpleWhitespace eaae70a4-cdca-491a-b2b3-7997d003b3c3
# cst-node-id 0.4.9.7.4.4.1.1.4.1 Name be0fd21d-beb1-4ebd-af96-3d68a2e25bda
# cst-node-id 0.4.9.7.4.4.1.1.4.2 Comma 679077f6-6207-4cab-9bb2-b323db3c5c78
# cst-node-id 0.4.9.7.4.4.1.1.4.2.0 SimpleWhitespace 8ea994b7-e4a5-45a5-b382-fe4b46d90518
# cst-node-id 0.4.9.7.4.4.1.1.4.2.1 SimpleWhitespace b701e55b-860e-43a8-a00a-35160e2cad90
# cst-node-id 0.4.9.7.4.4.1.1.4.3 SimpleWhitespace 0f7223ab-db2a-42f7-b595-c4ef2ef8f272
# cst-node-id 0.4.9.7.4.4.1.1.5 Arg 050c8f3c-9dc5-4331-84f8-41e825d311ba
# cst-node-id 0.4.9.7.4.4.1.1.5.0 SimpleWhitespace e0e9bed0-74d3-4d35-b474-6f403e382311
# cst-node-id 0.4.9.7.4.4.1.1.5.1 Name fbd5d241-31df-4941-9ff6-f54cf61f88d2
# cst-node-id 0.4.9.7.4.4.1.1.5.2 Comma 9bfceb78-e583-47e0-83a7-8c34cf2848e6
# cst-node-id 0.4.9.7.4.4.1.1.5.2.0 SimpleWhitespace 3b245533-7a09-4360-94c8-476c45542a26
# cst-node-id 0.4.9.7.4.4.1.1.5.2.1 SimpleWhitespace 6ce69549-d4f0-4a1d-a202-a3a51b144e94
# cst-node-id 0.4.9.7.4.4.1.1.5.3 SimpleWhitespace 848dd3b2-f964-4131-a907-e7660c4cddac
# cst-node-id 0.4.9.7.4.4.1.1.6 Arg 1b7cd6b8-3835-48b2-a702-2b8133cfaeed
# cst-node-id 0.4.9.7.4.4.1.1.6.0 SimpleWhitespace 27aceef4-8219-4129-8595-9f546f6c7334
# cst-node-id 0.4.9.7.4.4.1.1.6.1 Name bcb625c4-036b-4916-bc0a-5ac5ffa0d641
# cst-node-id 0.4.9.7.4.4.1.1.6.2 AssignEqual 437468df-67b4-4c9f-804c-e1745166de30
# cst-node-id 0.4.9.7.4.4.1.1.6.2.0 SimpleWhitespace 465cdc71-b536-4f00-9556-d9e6d9ee474d
# cst-node-id 0.4.9.7.4.4.1.1.6.2.1 SimpleWhitespace f82caba5-e8b0-41c1-8c7a-1359ee327087
# cst-node-id 0.4.9.7.4.4.1.1.6.3 Attribute af01c24c-6e00-4249-99e7-01fe2aed4759
# cst-node-id 0.4.9.7.4.4.1.1.6.3.0 Name 63cf18bb-5c36-42c3-81de-19e13630f7f5
# cst-node-id 0.4.9.7.4.4.1.1.6.3.1 Dot cdadb49f-c2fb-49ab-b2db-4835f6270d10
# cst-node-id 0.4.9.7.4.4.1.1.6.3.1.0 SimpleWhitespace 8109bad5-bb6b-4dbd-9a30-a20fea75b58f
# cst-node-id 0.4.9.7.4.4.1.1.6.3.1.1 SimpleWhitespace 557e0d40-0d8a-43cb-aa68-52bdaa51d75c
# cst-node-id 0.4.9.7.4.4.1.1.6.3.2 Name bc151f65-c521-4d75-a612-9650842336f6
# cst-node-id 0.4.9.7.4.4.1.1.6.4 SimpleWhitespace f48d9951-d092-41a9-9154-f970e77f67bc
# cst-node-id 0.4.9.7.4.4.2 TrailingWhitespace a738e477-e00d-4b1c-a2c8-42555052514f
# cst-node-id 0.4.9.7.4.4.2.0 SimpleWhitespace 4630776e-7bf3-4387-9375-f15189b3ca5d
# cst-node-id 0.4.9.7.4.4.2.1 Newline ba6b6aa0-abc7-4bb9-bfff-3f9d80193d77
# cst-node-id 0.4.9.7.4.5 With 753a8837-c9f4-4828-a7dd-ec3bec6fc6e5
# cst-node-id 0.4.9.7.4.5.0 EmptyLine 84f80675-36e8-493f-9cbf-1ab8c9f9922a
# cst-node-id 0.4.9.7.4.5.0.0 SimpleWhitespace 35c7bbef-8f5b-4e0c-bd34-a13858dae08b
# cst-node-id 0.4.9.7.4.5.0.1 Newline ec3dd3ba-3084-4002-a1d0-d3526a923400
# cst-node-id 0.4.9.7.4.5.1 EmptyLine d4135cad-920e-4950-a9e2-ba9335625c6a
# cst-node-id 0.4.9.7.4.5.1.0 SimpleWhitespace 12c1547d-5457-4971-843f-add0b1f50df8
# cst-node-id 0.4.9.7.4.5.1.1 Comment ba0330fe-71fc-4802-80b1-071804fe2dc2
# cst-node-id 0.4.9.7.4.5.1.2 Newline 8cb0888d-01ac-422c-bf4c-92fc3bb34487
# cst-node-id 0.4.9.7.4.5.2 SimpleWhitespace dd38a350-1ed4-45c3-a330-e496a52eb757
# cst-node-id 0.4.9.7.4.5.3 WithItem 4c8ae18e-f39a-4f54-a4ef-ddb3d2318992
# cst-node-id 0.4.9.7.4.5.3.0 Call 7a5451a8-b88a-4730-b69f-5db4c43c81c1
# cst-node-id 0.4.9.7.4.5.3.0.0 Name 204d6c41-a755-4117-a389-aca87ef0ad40
# cst-node-id 0.4.9.7.4.5.3.0.1 SimpleWhitespace 604ca3f1-3687-4879-8b63-d091e66ba5dd
# cst-node-id 0.4.9.7.4.5.3.0.2 SimpleWhitespace 4e3a499c-aa9f-4ffd-8af7-10ac45e02a0e
# cst-node-id 0.4.9.7.4.5.3.0.3 Arg addbaa0c-0317-4f90-89b5-4244cfbe91ee
# cst-node-id 0.4.9.7.4.5.3.0.3.0 SimpleWhitespace ed0d07f7-ee27-43f9-8737-7b9bcabf64d2
# cst-node-id 0.4.9.7.4.5.3.0.3.1 Name 12b83fb3-4348-4c9a-96cc-b4c39978e118
# cst-node-id 0.4.9.7.4.5.3.0.3.2 Comma b50f316d-1d55-451b-8178-43cad1703126
# cst-node-id 0.4.9.7.4.5.3.0.3.2.0 SimpleWhitespace 8e6c6390-0317-4285-bc2e-e010018d9451
# cst-node-id 0.4.9.7.4.5.3.0.3.2.1 SimpleWhitespace b2384045-d997-4ca1-bf2d-3e494dc075ae
# cst-node-id 0.4.9.7.4.5.3.0.3.3 SimpleWhitespace 3f4b8456-5ad9-4d28-9fab-4294b4589577
# cst-node-id 0.4.9.7.4.5.3.0.4 Arg e7f225b9-1ff8-46d5-864c-60cceb2ec868
# cst-node-id 0.4.9.7.4.5.3.0.4.0 SimpleWhitespace 9a977d72-ae8c-481d-b38f-179131dd20c7
# cst-node-id 0.4.9.7.4.5.3.0.4.1 SimpleString b6c481aa-bf91-40e0-bbf6-672b218d5091
# cst-node-id 0.4.9.7.4.5.3.0.4.2 Comma 519e71a6-debc-4213-b167-02c61a5f2938
# cst-node-id 0.4.9.7.4.5.3.0.4.2.0 SimpleWhitespace 24a37d82-f899-4398-ad3c-97803ecc0189
# cst-node-id 0.4.9.7.4.5.3.0.4.2.1 SimpleWhitespace a6183e22-5a77-4a8a-829b-620dbd6ba223
# cst-node-id 0.4.9.7.4.5.3.0.4.3 SimpleWhitespace c54323ea-31c3-4286-91b9-b2ee0575d1e0
# cst-node-id 0.4.9.7.4.5.3.0.5 Arg 9b09e891-3781-42fe-a90e-9cb85a038134
# cst-node-id 0.4.9.7.4.5.3.0.5.0 SimpleWhitespace 1278b5bf-62ea-4803-a8cd-261393278c19
# cst-node-id 0.4.9.7.4.5.3.0.5.1 Name 30ef1f9f-3a22-43d9-a420-c42e8f49c10f
# cst-node-id 0.4.9.7.4.5.3.0.5.2 AssignEqual 5c05a6ce-84d4-405b-bce9-151b0898b857
# cst-node-id 0.4.9.7.4.5.3.0.5.2.0 SimpleWhitespace da9fe2a1-3977-4475-9ec8-5b0ae2fa5fe3
# cst-node-id 0.4.9.7.4.5.3.0.5.2.1 SimpleWhitespace e6bb9dd8-b128-4346-83bd-04537e6e33c3
# cst-node-id 0.4.9.7.4.5.3.0.5.3 SimpleString fb80fd8f-7930-41ea-a26b-b56ea4bb8e47
# cst-node-id 0.4.9.7.4.5.3.0.5.4 SimpleWhitespace 3080f298-ffeb-4f30-82c2-faaf8679fc86
# cst-node-id 0.4.9.7.4.5.3.1 AsName 241194a2-d177-4d2e-a47a-9cad29da1e5a
# cst-node-id 0.4.9.7.4.5.3.1.0 SimpleWhitespace ad956b86-a3e7-4980-a557-518d3262d287
# cst-node-id 0.4.9.7.4.5.3.1.1 Name f8a47d15-7d9d-482c-b357-d476fa72cd67
# cst-node-id 0.4.9.7.4.5.3.1.2 SimpleWhitespace cf3a6fe6-3093-4224-b686-7a37ccb15967
# cst-node-id 0.4.9.7.4.5.4 SimpleWhitespace aca22b8e-2ef2-4fdb-9818-ae826378ad18
# cst-node-id 0.4.9.7.4.5.5 IndentedBlock 50843a80-68ae-4a87-9f07-b03ea99a883f
# cst-node-id 0.4.9.7.4.5.5.0 TrailingWhitespace 353ce478-f7ba-4a68-acf3-5cdc055dcb5a
# cst-node-id 0.4.9.7.4.5.5.0.0 SimpleWhitespace 02bd3e41-5fc1-441f-ba58-e379a2488f9a
# cst-node-id 0.4.9.7.4.5.5.0.1 Newline 79a42974-9355-4001-ad46-cf351edf73ba
# cst-node-id 0.4.9.7.4.5.5.1 SimpleStatementLine cd532032-bb05-4ab2-8259-0da52ccab31a
# cst-node-id 0.4.9.7.4.5.5.1.0 Expr acd26d2c-fb39-4528-a26c-30f1768bd7aa
# cst-node-id 0.4.9.7.4.5.5.1.0.0 Call 5e3ea82f-32f4-4a03-93b4-079b067447dd
# cst-node-id 0.4.9.7.4.5.5.1.0.0.0 Attribute c9fae898-b2c6-4375-abe6-83b0369a7863
# cst-node-id 0.4.9.7.4.5.5.1.0.0.0.0 Name 5539b7aa-258b-4f57-bdea-d7937a8b45d1
# cst-node-id 0.4.9.7.4.5.5.1.0.0.0.1 Dot 265aa12f-1a51-429e-bd90-7f096c176180
# cst-node-id 0.4.9.7.4.5.5.1.0.0.0.1.0 SimpleWhitespace 09e376d7-26cd-4113-8515-42fa05ca062b
# cst-node-id 0.4.9.7.4.5.5.1.0.0.0.1.1 SimpleWhitespace 23f80dcf-85e7-4224-8691-f5bd5f2bec57
# cst-node-id 0.4.9.7.4.5.5.1.0.0.0.2 Name 69f779ff-e2a2-4819-b80e-e534383563cf
# cst-node-id 0.4.9.7.4.5.5.1.0.0.1 SimpleWhitespace 470ec9ed-ffc9-42bb-8172-ff46c04cf780
# cst-node-id 0.4.9.7.4.5.5.1.0.0.2 SimpleWhitespace 8b8f36a9-c064-4d77-a0d1-3021d1053cbf
# cst-node-id 0.4.9.7.4.5.5.1.0.0.3 Arg 5bc438c7-4a87-4309-b9aa-d1b321076e6a
# cst-node-id 0.4.9.7.4.5.5.1.0.0.3.0 SimpleWhitespace dfba3795-824b-42f3-9c73-851c3b6e40f1
# cst-node-id 0.4.9.7.4.5.5.1.0.0.3.1 Name 38b9bfd0-1a34-47dc-a20b-e66f0975e647
# cst-node-id 0.4.9.7.4.5.5.1.0.0.3.2 SimpleWhitespace e3863585-d461-4d94-830c-2e5075be2bfc
# cst-node-id 0.4.9.7.4.5.5.1.1 TrailingWhitespace 8f5e9d03-9495-427c-a691-6d08866f5376
# cst-node-id 0.4.9.7.4.5.5.1.1.0 SimpleWhitespace 25102f81-2d44-4de6-a091-f0a0168df48d
# cst-node-id 0.4.9.7.4.5.5.1.1.1 Newline 02456a19-d1d4-4ce5-b865-ed68b3610bba
# cst-node-id 0.4.9.7.4.6 SimpleStatementLine 677304cc-0a74-49e2-ba2b-b9fcf30a85a5
# cst-node-id 0.4.9.7.4.6.0 EmptyLine 105dd659-346a-417a-9ee9-74996cfc6d03
# cst-node-id 0.4.9.7.4.6.0.0 SimpleWhitespace 42431444-ff96-452e-9619-68afcceee41c
# cst-node-id 0.4.9.7.4.6.0.1 Newline a4ac3606-71f9-451b-8dde-48bc6a3c040a
# cst-node-id 0.4.9.7.4.6.1 Expr 34e1aadb-c72b-4507-9453-7e079f06ece7
# cst-node-id 0.4.9.7.4.6.1.0 Call 6ae84684-ba1f-4120-b5e5-698d588594e7
# cst-node-id 0.4.9.7.4.6.1.0.0 Name 85c050e1-4513-4295-9329-626a217110d4
# cst-node-id 0.4.9.7.4.6.1.0.1 SimpleWhitespace 5202b86c-f0b1-46c5-ac2d-a0757df2f1ec
# cst-node-id 0.4.9.7.4.6.1.0.2 SimpleWhitespace b994f810-b29a-4c68-b88a-5c7d161ef249
# cst-node-id 0.4.9.7.4.6.1.0.3 Arg 64092a1b-ce9a-4e20-9ce2-5d97fd889ebd
# cst-node-id 0.4.9.7.4.6.1.0.3.0 SimpleWhitespace fcd2bac4-3a35-48de-a8c2-60bca105c239
# cst-node-id 0.4.9.7.4.6.1.0.3.1 FormattedString 484b750c-a5b5-4429-a32a-6e1d87fca0ec
# cst-node-id 0.4.9.7.4.6.1.0.3.1.0 FormattedStringText 12140b12-e9b9-4589-8096-4041b54cafb6
# cst-node-id 0.4.9.7.4.6.1.0.3.2 SimpleWhitespace 29d99e26-097b-4d08-b01c-64652718848a
# cst-node-id 0.4.9.7.4.6.2 TrailingWhitespace 6c8b36bc-6b18-47a5-aa89-8dc61feb2d28
# cst-node-id 0.4.9.7.4.6.2.0 SimpleWhitespace 6899a9e2-9e90-4c19-b921-4562d7bcdb99
# cst-node-id 0.4.9.7.4.6.2.1 Newline 9b46f274-7089-4397-8ed6-e87dc4984c79
# cst-node-id 0.4.9.7.4.7 SimpleStatementLine 716129e4-77ac-4927-97db-cbea0b951d85
# cst-node-id 0.4.9.7.4.7.0 Return f2e99fae-d7ce-4313-9569-b68b29a2f144
# cst-node-id 0.4.9.7.4.7.0.0 SimpleWhitespace 39fdc5b3-04cb-4700-ae36-e4fd955b0372
# cst-node-id 0.4.9.7.4.7.0.1 Name 101f047c-f0a4-4066-949b-6cb823e43fb5
# cst-node-id 0.4.9.7.4.7.1 TrailingWhitespace 9dde6e5c-499e-43fa-8640-b0f20e440266
# cst-node-id 0.4.9.7.4.7.1.0 SimpleWhitespace d04cecf9-dcea-44a8-b98b-303e6d9651c4
# cst-node-id 0.4.9.7.4.7.1.1 Newline bec262e9-c751-4172-ad9c-6f920684a62e
# cst-node-id 0.4.9.7.5 Else ae8554fd-5a80-43b4-9664-35f61b54cd55
# cst-node-id 0.4.9.7.5.0 SimpleWhitespace cdf4a093-e961-4791-a6d0-cf0eb0063b96
# cst-node-id 0.4.9.7.5.1 IndentedBlock c500470e-a17b-4a37-8581-b90257bea732
# cst-node-id 0.4.9.7.5.1.0 TrailingWhitespace 6a2be662-4220-4479-be8a-8f8edaf04267
# cst-node-id 0.4.9.7.5.1.0.0 SimpleWhitespace 6f599fc3-7e0b-4495-8194-593c3a010750
# cst-node-id 0.4.9.7.5.1.0.1 Newline b074e430-964c-4b73-9224-2ea240f98c3d
# cst-node-id 0.4.9.7.5.1.1 SimpleStatementLine 2911eb77-3d9b-4cf1-a506-d15488bc34ae
# cst-node-id 0.4.9.7.5.1.1.0 Expr 45bb6453-dcb8-44d2-996d-ac5544687b9f
# cst-node-id 0.4.9.7.5.1.1.0.0 Call 65e9d2ee-bc5b-4748-88d2-2d34cb113ee1
# cst-node-id 0.4.9.7.5.1.1.0.0.0 Name ec9bd563-0a44-4bbb-96b2-c29c30fc58ce
# cst-node-id 0.4.9.7.5.1.1.0.0.1 SimpleWhitespace 46fd5027-57b5-4d5e-b3d5-86b969f25ad6
# cst-node-id 0.4.9.7.5.1.1.0.0.2 SimpleWhitespace 051b6bd0-0545-4f48-a51b-04b4241b7e65
# cst-node-id 0.4.9.7.5.1.1.0.0.3 Arg 9c101ac4-53a4-40bf-a135-87bbcf03b2eb
# cst-node-id 0.4.9.7.5.1.1.0.0.3.0 SimpleWhitespace 47094bfe-c481-40b4-a84b-2b2f9e366f6b
# cst-node-id 0.4.9.7.5.1.1.0.0.3.1 FormattedString 73fc013b-28ba-4fa3-bde0-b046972bef77
# cst-node-id 0.4.9.7.5.1.1.0.0.3.1.0 FormattedStringText 582ba786-c044-40cd-b4d6-4803fdcee54f
# cst-node-id 0.4.9.7.5.1.1.0.0.3.2 SimpleWhitespace cdc0cd29-52b5-4f3a-8a46-18e4e3bc2d61
# cst-node-id 0.4.9.7.5.1.1.1 TrailingWhitespace 29ead156-9c76-4389-ae76-f8c30f5442ba
# cst-node-id 0.4.9.7.5.1.1.1.0 SimpleWhitespace 10e2549d-c039-4d8e-b084-9629693b78c6
# cst-node-id 0.4.9.7.5.1.1.1.1 Newline 92148f9a-ac36-41ff-abcc-bdd7dce1efaf
# cst-node-id 0.4.9.7.5.1.2 SimpleStatementLine 664049e8-19fa-4cf5-9599-d84c0aeaa864
# cst-node-id 0.4.9.7.5.1.2.0 Return 9d385ec7-bef9-4c71-9e8e-67028212d563
# cst-node-id 0.4.9.7.5.1.2.0.0 SimpleWhitespace 9dda2265-f1c5-43f0-be1c-24e11a57c19d
# cst-node-id 0.4.9.7.5.1.2.0.1 Name 165fb3ba-4c45-4ae9-b3b0-0ab088cdb373
# cst-node-id 0.4.9.7.5.1.2.1 TrailingWhitespace d175f43a-5e1c-4cdb-a49a-fb180c42d836
# cst-node-id 0.4.9.7.5.1.2.1.0 SimpleWhitespace cf52cfba-4df3-43ea-b4fa-674d7d9b2e3b
# cst-node-id 0.4.9.7.5.1.2.1.1 Newline fbf5d929-775e-4027-8af9-abccb0f797a5
# cst-node-id 0.5 FunctionDef 2189a6e9-dbfc-4b87-99dd-a7e164c70068
# cst-node-id 0.5.0 EmptyLine 6044bb8e-ee5c-4a64-8c24-ae3941c7721e
# cst-node-id 0.5.0.0 SimpleWhitespace 1e2cba48-7e1d-44b9-a63d-3231a0a6722c
# cst-node-id 0.5.0.1 Newline d5ab4ae3-bab7-4bfa-bcd8-29eb7c8ec99f
# cst-node-id 0.5.1 EmptyLine 855c58bd-e6e8-4920-8ac7-04f46ce21beb
# cst-node-id 0.5.1.0 SimpleWhitespace c523340b-a0f6-47c2-a638-423082537458
# cst-node-id 0.5.1.1 Newline b17a6e41-4cfb-4020-8478-ed6a9e31a1b3
# cst-node-id 0.5.2 SimpleWhitespace 70e371e3-86c4-4bde-b963-ffea78651c53
# cst-node-id 0.5.3 Name 87b5e818-34c5-42b5-9226-84f7492be256
# cst-node-id 0.5.4 SimpleWhitespace 5728f607-78d0-4a2f-a9cb-2715a8d3f586
# cst-node-id 0.5.5 SimpleWhitespace aefa3fe9-ba8f-48ea-a49f-2f3682deed53
# cst-node-id 0.5.6 SimpleWhitespace 024f47f0-ffd1-4cba-9fce-e9d084cbbca7
# cst-node-id 0.5.7 Parameters 7927152e-31a7-4414-95d1-d36260474f2b
# cst-node-id 0.5.8 Annotation bfb0378f-c1ca-4e68-b7e0-c3c04bbe1c54
# cst-node-id 0.5.8.0 SimpleWhitespace 0d2096a0-9f30-4eeb-8c32-9fd7a9a90c9c
# cst-node-id 0.5.8.1 SimpleWhitespace 6cd3b39d-8d65-4005-a6e2-f04fd25ac85f
# cst-node-id 0.5.8.2 Name 0be355df-4ae0-4f05-a88d-895e7c0dfa4a
# cst-node-id 0.5.9 SimpleWhitespace 87cfa84f-d742-4407-b94c-fee7164d5a3e
# cst-node-id 0.5.10 IndentedBlock 95357535-bbc2-432d-9770-834a8524d0fb
# cst-node-id 0.5.10.0 TrailingWhitespace 63507d6f-4ccc-40af-a391-3f474452b18b
# cst-node-id 0.5.10.0.0 SimpleWhitespace e925ee0b-9865-4f3e-b610-3218ddbfa30a
# cst-node-id 0.5.10.0.1 Newline bbe2f93b-0313-44af-8a4b-5bc64b478d72
# cst-node-id 0.5.10.1 SimpleStatementLine 5a8be4b4-bd2f-476e-856b-ca94e3824d90
# cst-node-id 0.5.10.1.0 Expr 73c193c9-841a-4149-af7e-9bca1ef46bb9
# cst-node-id 0.5.10.1.0.0 SimpleString 44aa1b1f-c43e-44f9-ba23-8523388b3eae
# cst-node-id 0.5.10.1.1 TrailingWhitespace afcd11e5-32e7-4e89-9fd0-202237471976
# cst-node-id 0.5.10.1.1.0 SimpleWhitespace e7a50042-7650-4a84-ade6-a914e55491ed
# cst-node-id 0.5.10.1.1.1 Newline 5def22bc-2367-4e3f-a9ae-1fc0d5d4cbd4
# cst-node-id 0.5.10.2 SimpleStatementLine 7334aaa8-435c-41e8-84b0-96feb1b6199f
# cst-node-id 0.5.10.2.0 Expr 002bb52d-d083-4e62-8921-9321a13c14a5
# cst-node-id 0.5.10.2.0.0 Call 7036a49b-0844-4dd5-9e7e-dc2484de49c5
# cst-node-id 0.5.10.2.0.0.0 Name fa5c8f67-ea18-4eae-9068-44ac58b75012
# cst-node-id 0.5.10.2.0.0.1 SimpleWhitespace 7000827e-3712-4880-8640-e973d224d0f3
# cst-node-id 0.5.10.2.0.0.2 SimpleWhitespace 3bbcc478-99d6-47d2-b9f4-94edfc5fa53e
# cst-node-id 0.5.10.2.0.0.3 Arg 37676009-bf45-4981-8997-916f5fda2f16
# cst-node-id 0.5.10.2.0.0.3.0 SimpleWhitespace 7859a2b0-922a-4410-9445-e0bc6d565de5
# cst-node-id 0.5.10.2.0.0.3.1 SimpleString 3ab94563-5b78-4746-9c5c-9bb1f926f555
# cst-node-id 0.5.10.2.0.0.3.2 SimpleWhitespace f331ad97-0b0f-4bc0-859a-50ed0836c6b0
# cst-node-id 0.5.10.2.1 TrailingWhitespace 58360b56-75cd-40ff-8ba0-f915e8529dd3
# cst-node-id 0.5.10.2.1.0 SimpleWhitespace ca101951-6fc6-4174-bf77-ba8fde2ac286
# cst-node-id 0.5.10.2.1.1 Newline 044f4ede-e939-4256-b1fd-cddfec987b3b
# cst-node-id 0.5.10.3 SimpleStatementLine 61aea9db-b83a-49e4-bf49-c37c3a7b1263
# cst-node-id 0.5.10.3.0 EmptyLine 2105ae94-fb11-440e-b13f-02d85ddc64d1
# cst-node-id 0.5.10.3.0.0 SimpleWhitespace e4034a5a-8046-42c4-aa9c-de1726bae743
# cst-node-id 0.5.10.3.0.1 Newline 6abee207-2753-410f-8b4e-51ed2b82cc0a
# cst-node-id 0.5.10.3.1 EmptyLine a77c7648-d481-4fc3-8ee3-cdf938c347d7
# cst-node-id 0.5.10.3.1.0 SimpleWhitespace a1c6c252-c009-42a9-9519-315b497e0492
# cst-node-id 0.5.10.3.1.1 Comment db48bd37-baf4-4e34-98f7-29ceb0c51394
# cst-node-id 0.5.10.3.1.2 Newline 6f8a46bc-4b4b-4629-9bbb-19913e532b9c
# cst-node-id 0.5.10.3.2 Assign 79ba5dfa-9646-4b34-85a3-17eb304dff3e
# cst-node-id 0.5.10.3.2.0 AssignTarget 7b1903ce-763e-4f37-942f-09d9898b812c
# cst-node-id 0.5.10.3.2.0.0 Name 30fc8814-964d-443e-8e90-9e16e703e728
# cst-node-id 0.5.10.3.2.0.1 SimpleWhitespace a88a32ec-7bc8-4768-9c6b-6adc7a8184a1
# cst-node-id 0.5.10.3.2.0.2 SimpleWhitespace 2d270329-622f-45c1-9aad-0936c0809270
# cst-node-id 0.5.10.3.2.1 Call 85b610b7-828a-422b-81f8-e1fbc0762e5e
# cst-node-id 0.5.10.3.2.1.0 Attribute 56f5d368-c03a-4005-9572-05f94e3a5fea
# cst-node-id 0.5.10.3.2.1.0.0 Name 820c67c9-6f19-4343-b575-b607c8ed6f18
# cst-node-id 0.5.10.3.2.1.0.1 Dot ecb1c099-8b40-464d-9e35-c8385321a2b0
# cst-node-id 0.5.10.3.2.1.0.1.0 SimpleWhitespace 18cda6c2-4081-419d-8cb1-01510967a849
# cst-node-id 0.5.10.3.2.1.0.1.1 SimpleWhitespace 670f0ab0-0657-4ca9-8469-3fbd390eb48a
# cst-node-id 0.5.10.3.2.1.0.2 Name 867f7d25-32e8-41cd-af3a-60a030bbed8c
# cst-node-id 0.5.10.3.2.1.1 SimpleWhitespace d9b0beb5-d72c-48f9-86c3-5a5ad3c26378
# cst-node-id 0.5.10.3.2.1.2 SimpleWhitespace b96b430e-0733-4e92-961f-ce9f269414bb
# cst-node-id 0.5.10.3.2.1.3 Arg 82a82f05-2217-48dd-85b5-1b4d2c7c45c6
# cst-node-id 0.5.10.3.2.1.3.0 SimpleWhitespace cce0e67e-8d1b-4c23-bad9-39c0c12bc7c4
# cst-node-id 0.5.10.3.2.1.3.1 SimpleString aed3ff3e-2b0e-4fa5-85ef-84453141ad62
# cst-node-id 0.5.10.3.2.1.3.2 SimpleWhitespace dad07317-1160-48ee-8ae7-90748cdd76dc
# cst-node-id 0.5.10.3.3 TrailingWhitespace b594c6f4-d32c-485d-b0f0-42e0cc652b47
# cst-node-id 0.5.10.3.3.0 SimpleWhitespace 4f13c4a4-1ff7-4758-9eff-8a34187226f3
# cst-node-id 0.5.10.3.3.1 Newline 9389db04-d046-4c53-8c34-3a0cbf31e577
# cst-node-id 0.5.10.4 SimpleStatementLine e0de27e6-3dcf-4653-aded-2ca46030c655
# cst-node-id 0.5.10.4.0 EmptyLine 0eaf7032-2a48-449e-81ba-8dedb46a6099
# cst-node-id 0.5.10.4.0.0 SimpleWhitespace 4a5c4f4b-eb76-408c-98d2-594864bb4cf9
# cst-node-id 0.5.10.4.0.1 Newline 47771b0f-5f0d-4cfb-a7d8-407a6b3632a0
# cst-node-id 0.5.10.4.1 Assign 0f4b664e-0a39-4b60-9054-74d429d078b2
# cst-node-id 0.5.10.4.1.0 AssignTarget 1ccfa2d7-81f6-463e-b515-db5363c01892
# cst-node-id 0.5.10.4.1.0.0 Name e6cf9328-24d6-4e0f-8ef9-7ed6cc39ea45
# cst-node-id 0.5.10.4.1.0.1 SimpleWhitespace daacefd6-db05-404d-9eed-5267451b4cc3
# cst-node-id 0.5.10.4.1.0.2 SimpleWhitespace a93c74ff-d0d7-46dc-a73f-118db7e5f5f2
# cst-node-id 0.5.10.4.1.1 Integer f13bd0b3-0466-47af-8538-b3f208489183
# cst-node-id 0.5.10.4.2 TrailingWhitespace 098a9041-8954-4e7a-9e86-035f9c860d8c
# cst-node-id 0.5.10.4.2.0 SimpleWhitespace bb9e2933-4ba0-4172-9a51-31901a963fba
# cst-node-id 0.5.10.4.2.1 Newline 24b1c670-fb0b-4092-b0c0-1c77adc076f8
# cst-node-id 0.5.10.5 For 6f12f9f1-f2a3-465f-a207-98902b9c503b
# cst-node-id 0.5.10.5.0 SimpleWhitespace 0e9212e0-6824-4c0c-b9b7-47c54b5fdb6f
# cst-node-id 0.5.10.5.1 Name 0258d7e1-369d-4381-b5af-cb0c7820da95
# cst-node-id 0.5.10.5.2 SimpleWhitespace d32c37c5-dbba-4845-9815-5843eb64299e
# cst-node-id 0.5.10.5.3 SimpleWhitespace 57c31ba3-3e58-4531-a6f9-91c2a3b2f2f3
# cst-node-id 0.5.10.5.4 Name 8174b295-2f37-4cc9-b824-c32a958dcd89
# cst-node-id 0.5.10.5.5 SimpleWhitespace 666fbc39-a7ac-4c7b-8b6d-19742ecfe82d
# cst-node-id 0.5.10.5.6 IndentedBlock 0a69e651-27fd-4704-a4b9-7ebf7a7fa5c4
# cst-node-id 0.5.10.5.6.0 TrailingWhitespace 65b3503c-2c24-431e-9de8-43a34fed9ed1
# cst-node-id 0.5.10.5.6.0.0 SimpleWhitespace 6222d233-794e-4fee-8d1f-f1068fa9e80a
# cst-node-id 0.5.10.5.6.0.1 Newline c4a8e39e-ca4a-411c-b8a3-5f004b6f23a7
# cst-node-id 0.5.10.5.6.1 If 52e0099c-2833-46fe-b342-d98387f7dc76
# cst-node-id 0.5.10.5.6.1.0 SimpleWhitespace f91279b6-82ec-4a09-a8ba-4d3f6a964ccb
# cst-node-id 0.5.10.5.6.1.1 Call 23d4b231-1117-4cf0-a6a4-7bf31813c4b8
# cst-node-id 0.5.10.5.6.1.1.0 Name 68842987-9689-4d38-9531-39a22430c836
# cst-node-id 0.5.10.5.6.1.1.1 SimpleWhitespace 3402aa13-210b-417a-966b-f66693f7532c
# cst-node-id 0.5.10.5.6.1.1.2 SimpleWhitespace 293a0744-5840-4609-a752-7fb4013c2af3
# cst-node-id 0.5.10.5.6.1.1.3 Arg d1d5d1ab-1333-41f6-8916-033dc80b1513
# cst-node-id 0.5.10.5.6.1.1.3.0 SimpleWhitespace bf8b0dbb-eb32-4853-82f0-8a12e7f14fa6
# cst-node-id 0.5.10.5.6.1.1.3.1 Name d2e7bc5d-863f-4a94-b864-41c6f2f066e9
# cst-node-id 0.5.10.5.6.1.1.3.2 SimpleWhitespace d0d3d70e-79e7-4b4d-abd8-1df4e6b385b5
# cst-node-id 0.5.10.5.6.1.2 SimpleWhitespace 6697f84d-de5a-4f7e-ba2d-537b95619697
# cst-node-id 0.5.10.5.6.1.3 IndentedBlock e016160d-1f95-4eba-ac1e-5cdd78475846
# cst-node-id 0.5.10.5.6.1.3.0 TrailingWhitespace 19d509f6-b61d-4dba-b69e-de35816cbf3d
# cst-node-id 0.5.10.5.6.1.3.0.0 SimpleWhitespace 3385ba8e-805b-4639-b4e2-31306ceec19d
# cst-node-id 0.5.10.5.6.1.3.0.1 Newline 34e2f0b7-c899-4547-9984-818fbe85206c
# cst-node-id 0.5.10.5.6.1.3.1 SimpleStatementLine 8e4ecaf8-4de8-453b-8ebc-1b0fe73a8361
# cst-node-id 0.5.10.5.6.1.3.1.0 AugAssign febb2cce-c914-40b3-ad0d-f0ec98692780
# cst-node-id 0.5.10.5.6.1.3.1.0.0 Name 2f29aba3-4498-409a-aa17-2ede064352b8
# cst-node-id 0.5.10.5.6.1.3.1.0.1 AddAssign 67f1ec75-d02e-49ef-b4f8-bc558063b48d
# cst-node-id 0.5.10.5.6.1.3.1.0.1.0 SimpleWhitespace b7603ba0-3b6e-4ef5-bdef-e020e3083fec
# cst-node-id 0.5.10.5.6.1.3.1.0.1.1 SimpleWhitespace 6c64aea2-9ae6-4ab9-b280-bf35f2838c57
# cst-node-id 0.5.10.5.6.1.3.1.0.2 Integer 76baef9b-52c2-47af-9652-5de73eeae0b1
# cst-node-id 0.5.10.5.6.1.3.1.1 TrailingWhitespace 82b16301-0eaf-4235-ad98-e76545d878e0
# cst-node-id 0.5.10.5.6.1.3.1.1.0 SimpleWhitespace fd21bbf7-2bbd-4e05-9e32-247625d8f602
# cst-node-id 0.5.10.5.6.1.3.1.1.1 Newline 537ec2bd-8d7a-4003-b461-a005ce7611de
# cst-node-id 0.5.10.6 SimpleStatementLine 4a4a501e-adf2-4ac2-88d7-7f9c3e5b2b89
# cst-node-id 0.5.10.6.0 EmptyLine 81486050-c303-4423-8408-cbca461d9664
# cst-node-id 0.5.10.6.0.0 SimpleWhitespace 08042f87-9b22-454f-9b8c-9570b4f9f5a9
# cst-node-id 0.5.10.6.0.1 Newline 42e249ab-accb-4951-bd5c-d40fd39620c5
# cst-node-id 0.5.10.6.1 Expr d62c6da6-e3be-4158-916b-59b00e5f0467
# cst-node-id 0.5.10.6.1.0 Call 63f7e071-0a2b-4faa-b6a6-c40ca15160a0
# cst-node-id 0.5.10.6.1.0.0 Name 85147b37-6c83-4d4c-8c2e-baacee688fb7
# cst-node-id 0.5.10.6.1.0.1 SimpleWhitespace 18a94fbf-7d37-4885-8ebd-8689dc068e78
# cst-node-id 0.5.10.6.1.0.2 SimpleWhitespace 72acb7c6-3544-4409-bfbc-f556097b0cb4
# cst-node-id 0.5.10.6.1.0.3 Arg 920d6fc4-a605-45a7-956d-e27cde7d042f
# cst-node-id 0.5.10.6.1.0.3.0 SimpleWhitespace 3704a374-2974-4ac4-b118-0e4e32fb80e4
# cst-node-id 0.5.10.6.1.0.3.1 FormattedString 95f74810-5b0d-4bd5-87a7-dc0e853fe90c
# cst-node-id 0.5.10.6.1.0.3.1.0 FormattedStringText f47474f9-e11b-4ce1-afb5-1b20ef3470bb
# cst-node-id 0.5.10.6.1.0.3.1.1 FormattedStringExpression 4d53e575-1959-4942-aea9-b14e59743d2a
# cst-node-id 0.5.10.6.1.0.3.1.1.0 SimpleWhitespace 6c1676bd-bf0e-4320-ae30-8256117cb086
# cst-node-id 0.5.10.6.1.0.3.1.1.1 Name 27aad5a9-08b6-4b7a-857e-2f0f0cdba767
# cst-node-id 0.5.10.6.1.0.3.1.1.2 SimpleWhitespace dfe4e7b9-9ff0-406b-bb0d-0e133bd03a92
# cst-node-id 0.5.10.6.1.0.3.1.2 FormattedStringText 5a62195d-68e8-4069-9162-a55ef2988c97
# cst-node-id 0.5.10.6.1.0.3.2 SimpleWhitespace b9c21258-5818-4922-b135-090e208609ef
# cst-node-id 0.5.10.6.2 TrailingWhitespace 91a85ae0-d75e-4739-8f38-d2a779a4334e
# cst-node-id 0.5.10.6.2.0 SimpleWhitespace cdbce276-74c2-4ad8-86e7-5147995762ec
# cst-node-id 0.5.10.6.2.1 Newline 2ddba548-dd85-4199-bf92-95925689e23d
# cst-node-id 0.5.10.7 EmptyLine 13c4ac5e-6d66-4c5c-935b-1a336c7f363b
# cst-node-id 0.5.10.7.0 SimpleWhitespace c16f69ad-2734-41e6-b4b2-c2f5ca21c381
# cst-node-id 0.5.10.7.1 Comment 982f63af-62b9-4037-a1ab-0f066eef351f
# cst-node-id 0.5.10.7.2 Newline 4a40cf2c-f041-4d05-8595-4ef052fbab29
# cst-node-id 0.6 If 13da4269-375e-4923-aa8a-82b5b43db587
# cst-node-id 0.6.0 EmptyLine b79d2362-ca14-4285-8870-dde9c417ca4f
# cst-node-id 0.6.0.0 SimpleWhitespace 82b24113-074a-4a4d-ba0f-aafb09f8493c
# cst-node-id 0.6.0.1 Newline cc80adb0-ff28-4e53-aaa9-a3f9c9022260
# cst-node-id 0.6.1 EmptyLine fc0e5db7-29c7-451c-afc1-f45052729749
# cst-node-id 0.6.1.0 SimpleWhitespace b7a546a3-337a-4b03-9369-5577e0a3bce0
# cst-node-id 0.6.1.1 Newline 380acd9b-ab2f-4e9c-be9a-6e2508b998cc
# cst-node-id 0.6.2 SimpleWhitespace d891c10a-4f80-421f-bac1-7ef5527db9b6
# cst-node-id 0.6.3 Comparison 7ee1d00c-5231-4cbb-b653-5bfd803de8c9
# cst-node-id 0.6.3.0 Name aa2749a9-48d5-46f4-8488-291f54cfc073
# cst-node-id 0.6.3.1 ComparisonTarget ec343806-2d3e-4044-b434-f08d4ef1f9ba
# cst-node-id 0.6.3.1.0 Equal ebb7be76-24cb-4f41-9e2e-1a6c648c053c
# cst-node-id 0.6.3.1.0.0 SimpleWhitespace d6cbe7c2-f8ae-4615-8ce9-15254231bfa7
# cst-node-id 0.6.3.1.0.1 SimpleWhitespace 461eeec4-8907-4d7f-80da-040f5d441d65
# cst-node-id 0.6.3.1.1 SimpleString d68fd1ee-cd26-4f4a-8799-2badd0ec69cf
# cst-node-id 0.6.4 SimpleWhitespace 7793ac19-11d0-4442-b3a3-27a889969ba4
# cst-node-id 0.6.5 IndentedBlock d754395f-6d5d-4472-b7a0-b50555d6175a
# cst-node-id 0.6.5.0 TrailingWhitespace 34079022-1c2f-4f1d-ae34-4f9a4895ba81
# cst-node-id 0.6.5.0.0 SimpleWhitespace 4936d36d-aa22-4004-a185-25d3fbd674cc
# cst-node-id 0.6.5.0.1 Newline c55bf7e4-e25e-4216-95f5-53bbf824a80d
# cst-node-id 0.6.5.1 SimpleStatementLine 3b5afd36-3a66-4fa3-8e32-3b6795bbe195
# cst-node-id 0.6.5.1.0 Expr b510116f-2806-4dbe-b4ce-0299648ddbcc
# cst-node-id 0.6.5.1.0.0 Call a11c1f29-ea67-414d-b876-3c1fe85e209c
# cst-node-id 0.6.5.1.0.0.0 Name 6a6e2e04-4044-40de-a628-4edb104102d3
# cst-node-id 0.6.5.1.0.0.1 SimpleWhitespace ad4f48b5-4cf2-4cea-bedd-ff109ddf488a
# cst-node-id 0.6.5.1.0.0.2 SimpleWhitespace b8f609a0-08c6-44a9-b88e-762d0662316b
# cst-node-id 0.6.5.1.1 TrailingWhitespace e01d1790-bed1-4ba2-ab44-39cd925f1638
# cst-node-id 0.6.5.1.1.0 SimpleWhitespace 2e8fff3e-0625-4265-ac53-9405969b1bf2
# cst-node-id 0.6.5.1.1.1 Newline 29b0a1c8-e0cf-4718-9dc2-648f00e3805a
# cst-node-id 0.7 EmptyLine 578df6e3-c22d-4017-8fc7-d058af63a5d9
# cst-node-id 0.7.0 SimpleWhitespace 578dc75c-e087-47b1-a77b-6cc3e232f161
# cst-node-id 0.7.1 Newline e68ff5ab-47bc-4d3d-9311-2f0d26cedc5b
# cst-node-id 0.8 EmptyLine ebcb864f-043e-41a0-946f-5007c9ed09ae
# cst-node-id 0.8.0 SimpleWhitespace 848f8c60-34c8-4436-ba56-0233ad7463bd
# cst-node-id 0.8.1 Newline 860027c8-d28a-4831-9c30-0563b1025284
# cst-node-id 0.9 EmptyLine 163f666e-d8cc-43ea-8846-e6e4737985c3
# cst-node-id 0.9.0 SimpleWhitespace a33d8b18-11dc-4db5-832a-d0ee829a2d81
# cst-node-id 0.9.1 Comment a0722bde-1969-4955-a0a3-4d4024106ab0
# cst-node-id 0.9.2 Newline 78e28907-0239-4a77-9c1c-1a1c40d6b9a4
# cst-node-ids: end
